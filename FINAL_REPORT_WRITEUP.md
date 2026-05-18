# MiniOS Safety And Deterministic Harness Handoff

## Source Scope

- Primary branch: `integration/deterministic-harness-base`
- Repository branch link: [https://github.com/Castellanos02/MiniOS/tree/integration/deterministic-harness-base](https://github.com/Castellanos02/MiniOS/tree/integration/deterministic-harness-base)
- Note: the branch may need to be pushed before the GitHub link resolves publicly.
- Local note: the scheduler policy work is present in the local integration work that was preserved before switching back to `main`; it should be treated as implemented local work that still needs normal branch handoff/push.

## How To Use This Document

This document is not meant to read like a traditional essay. It is a handoff document for future kernel integration.

Use it as:

- An implementation reflection describing what I built and why.
- An API/specification document for the deterministic harness.
- A test coverage summary for current host-side validation.
- A future integration guide for connecting this work into Axel's kernel code.

Implemented APIs are labeled as implemented and match the inspected code. Proposed wrappers are labeled as proposed and should not be treated as existing code until they are added.

## Main Focus Of My Work

My main contribution was building a safety and deterministic harness for MiniOS. The goal was to make the project easier to validate before deeper kernel integration. MiniOS has timing-sensitive behavior, proactive suggestions, alert routing, shutdown state, model/data logic, and scheduler work. Without repeatable contracts, changes in one area can silently break another.

The harness gives us a way to define expected behavior and test it on the host before relying on full OS boot testing. This supports safer integration, clearer debugging, and a cleaner handoff to future kernel work.

## Architecture Diagram

```text
                         MiniOS Safety + Deterministic Harness
================================================================================

                                  +----------------+
                                  |   Kernel Boot  |
                                  |  / kernel_main |
                                  +--------+-------+
                                           |
                                           v
                                  +----------------+
                                  |  runtime_init  |
                                  +--------+-------+
                                           |
                  +------------------------+------------------------+
                  |                        |                        |
                  v                        v                        v
        +------------------+     +------------------+     +------------------+
        | Deterministic    |     | Message Bus      |     | Boot Verifier    |
        | Clock            |     | Priority Lanes   |     | Marker Check     |
        +--------+---------+     +--------+---------+     +--------+---------+
                 |                        |                        |
                 |                        v                        |
                 |              +------------------+               |
                 |              | Alert Arbiter    |<--------------+
                 |              | Alert Routing    |
                 |              +--------+---------+
                 |                       |
                 |        +--------------+--------------+
                 |        |              |              |
                 v        v              v              v
        +------------+ +---------+ +-------------+ +-------------+
        | Watchdog   | | UI/Log  | | Shutdown    | | Diagnostics |
        | Heartbeats | | Sink    | | State Save  | | / Tests     |
        +------------+ +---------+ +-------------+ +-------------+


================================================================================
                         Deterministic Policy Layer
================================================================================

        +------------------+       +------------------+
        | Suggestion       |       | Scheduler Policy |
        | Policy           |       | Harness          |
        | - cadence        |       | - priority       |
        | - idle threshold |       | - sleep/wake     |
        | - anti-repeat    |       | - idle fallback  |
        +--------+---------+       +--------+---------+
                 |                          |
                 v                          v
        +------------------+       +------------------+
        | SNN Suggestion   |       | Kernel Scheduler |
        | Boundary         |       | / PIT / Tasks    |
        | Proposed wrapper |       | Future API work  |
        +------------------+       +------------------+


================================================================================
                         Research / Model Side
================================================================================

        +------------------------------+
        | research/neuromorphic_       |
        | assistant                    |
        +---------------+--------------+
                        |
                        v
        +------------------------------+
        | Dataset Contract             |
        | - 16 features                |
        | - 12 classes                 |
        | - fixed seed reproducibility |
        | - stable train/val/test      |
        +---------------+--------------+
                        |
                        v
        +------------------------------+
        | SNN Training / Export        |
        | Research-side workflow       |
        +------------------------------+
```

## Implementation Status Table

| Component | Status | Main Files | Test Target | Integration Need |
| --- | --- | --- | --- | --- |
| Deterministic clock | Implemented | `src/shared/clock.h`, `src/shared/clock.c` | Covered indirectly by message bus/watchdog tests | Kernel code should use this through shared services instead of wall-clock timing in host tests. |
| Message types | Implemented | `src/shared/message_types.h` | Covered by bus, watchdog, shutdown, boot tests | Team still needs final actor ID and message type conventions. |
| Message bus | Implemented | `src/shared/message_bus.h`, `src/shared/message_bus.c` | `make message-bus-test` | Kernel modules should post structured events through the bus. |
| Watchdog | Implemented | `src/shared/watchdog.h`, `src/shared/watchdog.c` | `make watchdog-alert-test` | Decide which kernel tasks/actors must register and heartbeat. |
| Alert arbiter | Implemented | `src/shared/alert_arbiter.h`, `src/shared/alert_arbiter.c` | `make watchdog-alert-test`, `make shutdown-test` | Decide where `alert_arbiter_process()` runs in the kernel loop/tick. |
| Shutdown state | Implemented | `src/shared/shutdown.h`, `src/shared/shutdown.c` | `make shutdown-test` | Decide kernel persistence path and what runtime state Axel's code owns. |
| Boot verifier | Implemented | `src/shared/boot_verifier.h`, `src/shared/boot_verifier.c` | `make boot-verifier-test` | Kernel boot should call set expected, set observed, then verify. |
| Runtime initialization | Implemented | `src/shared/runtime.h`, `src/shared/runtime.c` | `make runtime-test` | Kernel startup should call `runtime_init()` before using harness services. |
| Suggestion policy | Implemented | `src/shared/suggestion_policy.h`, `src/shared/suggestion_policy.c` | `make suggestion-policy-test` | Kernel/SNN path should use policy functions instead of duplicating cadence and anti-repeat logic. |
| Dataset contract | Implemented | `research/neuromorphic_assistant/use_case_data.py`, `tests/research/dataset_contract_test.py` | `make dataset-contract-test` | SNN inference boundary still needs to be defined for kernel use. |
| Scheduler policy | Implemented in local integration work | `src/shared/scheduler_policy.h`, `src/shared/scheduler_policy.c` | `make scheduler-policy-test` | Decide whether this remains host-side validation only or becomes the kernel scheduling contract. |
| Compliance test | Implemented in local integration work | `Makefile` | `make compliance-test` | Team should require this before future integration merges. |

## Implemented API Contracts

### Deterministic Clock

Files: `src/shared/clock.h`, `src/shared/clock.c`

Purpose: provide a deterministic millisecond clock for tests and shared runtime behavior. Other harness modules use this instead of wall-clock time.

Implemented APIs:

`void clock_reset(uint64_t now_ms)`

- Purpose: resets the deterministic clock to a known timestamp.
- Parameters: `now_ms`, the new current time in milliseconds.
- Returns: nothing.
- Calling purpose: test setup and runtime reset.

`uint64_t clock_now_ms(void)`

- Purpose: returns the current deterministic time.
- Parameters: none.
- Returns: current time in milliseconds.
- Calling purpose: timestamping messages and checking watchdog deadlines.

`void clock_set_now_ms(uint64_t now_ms)`

- Purpose: replaces the current deterministic time.
- Parameters: `now_ms`, the exact millisecond value to use.
- Returns: nothing.
- Calling purpose: tests that need exact simulated time.

`void clock_advance_ms(uint64_t delta_ms)`

- Purpose: advances deterministic time by a fixed delta.
- Parameters: `delta_ms`, milliseconds to add.
- Returns: nothing.
- Calling purpose: tests that simulate time passing without real waiting.

Example:

```c
clock_reset(0);
clock_advance_ms(250);
if (clock_now_ms() != 250) {
    return -1;
}
```

### Message Types

File: `src/shared/message_types.h`

Purpose: define the common message format, priorities, message type enum, bus stats structure, and trace event structure.

Implemented constants:

```c
#define MSG_PRIO_LOW 0
#define MSG_PRIO_NORMAL 1
#define MSG_PRIO_ALERT 2
#define MSG_PRIO_CRITICAL 3
```

Implemented message struct:

```c
typedef struct {
    uint8_t priority;
    uint16_t type;
    uint32_t sender_id;
    uint64_t timestamp_ms;
    uint8_t payload[128];
} Message;
```

Important fields:

- `priority`: lane/urgency for bus ordering.
- `type`: semantic message type, using `MessageType` values such as `MSG_TYPE_BOOT_VERIFY`, `MSG_TYPE_CRASH`, `MSG_TYPE_SHUTDOWN`, and `MSG_TYPE_NEURO_SUGGESTION`.
- `sender_id`: actor or module that created the message. Final team-wide actor IDs are still open.
- `timestamp_ms`: timestamp in deterministic milliseconds. If this is `0`, `message_bus_post()` stamps it with `clock_now_ms()`.
- `payload[128]`: bounded payload bytes for short status text or event data.

### Message Bus

Files: `src/shared/message_bus.h`, `src/shared/message_bus.c`

Purpose: provide priority-based, bounded, traceable runtime communication.

Implemented behavior:

- Four priority lanes are used, each with capacity 64.
- Drain order is critical, alert, normal, low.
- Low, normal, and alert lanes overwrite oldest entries when full.
- Critical lane rejects overflow instead of overwriting.
- Zero timestamps are replaced with deterministic clock time.
- Post and drain operations are recorded in a trace buffer with capacity 256.

Implemented APIs:

`int message_bus_init(void)`

- Purpose: initializes the message bus.
- Parameters: none.
- Returns: `0` on success, `-1` if already initialized.
- Calling purpose: runtime/test startup after reset.

`void message_bus_reset(void)`

- Purpose: clears lanes, counters, traces, and initialization state.
- Parameters: none.
- Returns: nothing.
- Calling purpose: test setup and runtime reset.

`int message_bus_post(const Message* message)`

- Purpose: posts a message into the correct priority lane.
- Parameters: `message`, pointer to the message to enqueue.
- Returns: `0` on success, `-1` if uninitialized, input is null, priority is invalid, or critical lane overflow occurs.
- Calling purpose: modules publish alerts, boot status, watchdog failures, debug events, and diagnostics.

`int message_bus_peek_next(Message* out)`

- Purpose: copies the next highest-priority message without removing it.
- Parameters: `out`, output message pointer.
- Returns: `1` if a message is available, `0` if no message is available or the bus/output is invalid.
- Calling purpose: alert arbiter inspection before draining.

`int message_bus_drain_next(Message* out)`

- Purpose: removes and returns the next highest-priority message.
- Parameters: `out`, output message pointer.
- Returns: `1` if drained, `0` if no message is available or bus/output is invalid.
- Calling purpose: consumers, tests, logging, diagnostics.

`void message_bus_stats(uint32_t* dropped, uint32_t* total_posted)`

- Purpose: copies current dropped/rejected and total post attempt counters.
- Parameters: `dropped` and `total_posted`, optional output pointers.
- Returns: nothing.
- Calling purpose: tests and diagnostics. Note: `MessageBusStats` includes `drained`, but this API only exposes dropped and total posted.

`void message_bus_trace_clear(void)`

- Purpose: clears the trace buffer.
- Parameters: none.
- Returns: nothing.
- Calling purpose: tests that need a clean trace.

`size_t message_bus_trace_copy(BusTraceEvent* out, size_t max_events)`

- Purpose: copies trace events into caller storage.
- Parameters: `out`, output trace buffer; `max_events`, maximum events to copy.
- Returns: number of events copied.
- Calling purpose: tests/debugging to inspect post/drain history.

Safe example:

```c
Message msg = {0};
msg.priority = MSG_PRIO_CRITICAL;
msg.type = MSG_TYPE_CRASH;
msg.sender_id = 1;

if (message_bus_post(&msg) != 0) {
    return -1;
}
```

### Watchdog

Files: `src/shared/watchdog.h`, `src/shared/watchdog.c`

Purpose: monitor registered actors for missed heartbeats and emit deterministic critical messages.

Implemented constants and struct:

```c
#define WATCHDOG_NAME_MAX 32
#define WATCHDOG_MAX_ACTORS 16

typedef struct {
    uint32_t actor_id;
    char name[WATCHDOG_NAME_MAX];
    uint64_t heartbeat_interval_ms;
    uint64_t last_heartbeat_ms;
    uint64_t missed_alerts;
    uint8_t registered;
    uint8_t alert_active;
} WatchdogActorInfo;
```

Implemented APIs:

`int watchdog_init(void)`

- Purpose: initializes watchdog state.
- Parameters: none.
- Returns: `0` on success, `-1` if already initialized.
- Calling purpose: runtime/test startup.

`void watchdog_reset(void)`

- Purpose: clears all registered actors and initialization state.
- Parameters: none.
- Returns: nothing.
- Calling purpose: test setup and runtime reset.

`int watchdog_register(uint32_t actor_id, const char* name, uint64_t heartbeat_interval_ms)`

- Purpose: registers an actor for liveness monitoring.
- Parameters: `actor_id`, unique actor ID; `name`, bounded human-readable name; `heartbeat_interval_ms`, configured interval.
- Returns: `0` on success, `-1` if uninitialized, interval is zero, name is null, actor already exists, or actor capacity is full.
- Calling purpose: kernel task/subsystem startup.

`int watchdog_heartbeat(uint32_t actor_id)`

- Purpose: marks a registered actor as alive at the current deterministic time.
- Parameters: `actor_id`, registered actor ID.
- Returns: `0` on success, `-1` if uninitialized or actor is not registered.
- Calling purpose: task loops or periodic actor health updates.

`size_t watchdog_tick(void)`

- Purpose: checks all registered actors and emits critical messages for missed deadlines.
- Parameters: none.
- Returns: number of alerts emitted during this tick.
- Calling purpose: scheduler/timer loop or host tests.
- Implementation detail: current code emits when `now_ms >= last_heartbeat_ms + (heartbeat_interval_ms * 2)`. The configured interval is effectively doubled before alerting.

`int watchdog_get(uint32_t actor_id, WatchdogActorInfo* out)`

- Purpose: copies actor state for diagnostics/tests.
- Parameters: `actor_id`, registered actor ID; `out`, output pointer.
- Returns: `0` on success, `-1` if actor is missing or output is null.
- Calling purpose: tests and diagnostics.

### Alert Arbiter

Files: `src/shared/alert_arbiter.h`, `src/shared/alert_arbiter.c`

Purpose: route alert/critical messages from the bus to configured sinks.

Implemented callback type:

```c
typedef void (*AlertSink)(const Message* message, void* user_data);
```

Implemented APIs:

`int alert_arbiter_init(void)`

- Purpose: initializes alert arbiter state.
- Parameters: none.
- Returns: `0` on success, `-1` if already initialized.
- Calling purpose: runtime/test startup.

`void alert_arbiter_reset(void)`

- Purpose: clears sink bindings and initialization state.
- Parameters: none.
- Returns: nothing.
- Calling purpose: test setup and runtime reset.

`void alert_arbiter_set_log_sink(AlertSink sink, void* user_data)`

- Purpose: sets the log sink callback.
- Parameters: `sink`, callback or `NULL`; `user_data`, caller-owned context pointer.
- Returns: nothing.
- Calling purpose: runtime/test setup.

`void alert_arbiter_set_ui_sink(AlertSink sink, void* user_data)`

- Purpose: sets the UI sink callback.
- Parameters: `sink`, callback or `NULL`; `user_data`, caller-owned context pointer.
- Returns: nothing.
- Calling purpose: runtime/test setup.

`void alert_arbiter_set_shutdown_sink(AlertSink sink, void* user_data)`

- Purpose: sets the shutdown sink callback.
- Parameters: `sink`, callback or `NULL`; `user_data`, caller-owned context pointer.
- Returns: nothing.
- Calling purpose: runtime/test setup.

`size_t alert_arbiter_process(void)`

- Purpose: drains and dispatches alert/critical messages from the bus.
- Parameters: none.
- Returns: number of messages handled.
- Calling purpose: runtime loop, scheduler tick, or tests.
- Implementation detail: it processes while the next highest-priority message has priority `>= MSG_PRIO_ALERT`. Non-alert traffic remains on the bus.

Safe sink example:

```c
static void shutdown_sink(const Message* message, void* user_data) {
    (void)user_data;
    if (message != NULL) {
        (void)shutdown_record_critical(message);
    }
}
```

### Shutdown State

Files: `src/shared/shutdown.h`, `src/shared/shutdown.c`

Purpose: persist route/profile/media state and a bounded critical-message log for shutdown/recovery validation.

Implemented constants and struct:

```c
#define SHUTDOWN_ROUTE_MAX 64
#define SHUTDOWN_CRITICAL_LOG_MAX 8

typedef struct {
    char route[SHUTDOWN_ROUTE_MAX];
    uint32_t profile_id;
    uint64_t media_position_ms;
    Message critical_logs[SHUTDOWN_CRITICAL_LOG_MAX];
    size_t critical_log_count;
} ShutdownState;
```

Implemented APIs:

`int shutdown_init(void)`

- Purpose: initializes shutdown state.
- Parameters: none.
- Returns: `0` on success, `-1` if already initialized.
- Calling purpose: runtime/test startup.

`void shutdown_reset(void)`

- Purpose: clears shutdown state and initialization flag.
- Parameters: none.
- Returns: nothing.
- Calling purpose: runtime reset/test setup.

`int shutdown_set_route(const char* route)`

- Purpose: stores the current route string.
- Parameters: `route`, null-terminated route text. It is truncated to fit `SHUTDOWN_ROUTE_MAX`.
- Returns: `0` on success, `-1` if uninitialized or route is null.
- Calling purpose: route/session state update.

`int shutdown_set_profile_id(uint32_t profile_id)`

- Purpose: stores current profile ID.
- Parameters: `profile_id`, profile identifier.
- Returns: `0` on success, `-1` if uninitialized.
- Calling purpose: profile state update.

`int shutdown_set_media_position(uint64_t media_position_ms)`

- Purpose: stores current media position in milliseconds.
- Parameters: `media_position_ms`, media timestamp.
- Returns: `0` on success, `-1` if uninitialized.
- Calling purpose: media state update.

`int shutdown_record_critical(const Message* message)`

- Purpose: records an alert/critical message in the bounded critical log.
- Parameters: `message`, pointer to message with priority `>= MSG_PRIO_ALERT`.
- Returns: `0` on success, `-1` if uninitialized, message is null, or priority is below alert.
- Calling purpose: alert arbiter shutdown sink or direct critical handling.
- Implementation detail: if the log is full, the oldest entry is shifted out.

`size_t shutdown_critical_log_count(void)`

- Purpose: returns current number of critical logs.
- Parameters: none.
- Returns: log count.
- Calling purpose: tests/diagnostics.

`int shutdown_get_state(ShutdownState* out)`

- Purpose: copies current shutdown state.
- Parameters: `out`, output pointer.
- Returns: `0` on success, `-1` if output is null.
- Calling purpose: tests/diagnostics.

`int shutdown_flush(const char* path)`

- Purpose: writes shutdown state to a text file.
- Parameters: `path`, output file path.
- Returns: `0` on success, `-1` if uninitialized, path is null, or file cannot be opened.
- Calling purpose: controlled shutdown or failure capture.

`int shutdown_restore(const char* path)`

- Purpose: restores shutdown state from a text file.
- Parameters: `path`, input file path.
- Returns: `0` on success, `-1` if uninitialized, path is null, or file cannot be opened.
- Calling purpose: startup/recovery validation.

### Boot Verifier

Files: `src/shared/boot_verifier.h`, `src/shared/boot_verifier.c`

Purpose: compare expected and observed boot markers and post boot verification status to the message bus.

Implemented APIs:

`int boot_verifier_init(void)`

- Purpose: initializes verifier state.
- Parameters: none.
- Returns: `0` on success, `-1` if already initialized.
- Calling purpose: runtime/test startup.

`void boot_verifier_reset(void)`

- Purpose: clears expected marker, observed marker, verified state, and initialization flag.
- Parameters: none.
- Returns: nothing.
- Calling purpose: runtime reset/test setup.

`int boot_verifier_set_expected(uint32_t expected_marker)`

- Purpose: stores expected boot marker.
- Parameters: `expected_marker`, expected bootloader marker.
- Returns: `0` on success, `-1` if verifier is not initialized.
- Calling purpose: boot setup.

`int boot_verifier_set_observed(uint32_t observed_marker)`

- Purpose: stores observed boot marker.
- Parameters: `observed_marker`, marker received by kernel boot.
- Returns: `0` on success, `-1` if verifier is not initialized.
- Calling purpose: kernel boot after receiving bootloader value.

`int boot_verifier_verify(void)`

- Purpose: compares expected and observed markers.
- Parameters: none.
- Returns: `0` if verified, `-1` if uninitialized or markers fail verification.
- Calling purpose: boot verification step.
- Implementation detail: success requires `expected_marker != 0 && expected_marker == observed_marker`. It posts `MSG_TYPE_BOOT_VERIFY` with alert priority on success or critical priority on failure.

`int boot_verifier_is_verified(void)`

- Purpose: reads current verified state.
- Parameters: none.
- Returns: nonzero if verified, zero otherwise.
- Calling purpose: tests/diagnostics.

`uint32_t boot_verifier_expected(void)` and `uint32_t boot_verifier_observed(void)`

- Purpose: return stored marker values.
- Parameters: none.
- Returns: expected or observed marker.
- Calling purpose: tests/diagnostics.

Safe boot example:

```c
if (boot_verifier_set_expected(0x2BADB002) != 0) {
    return -1;
}
if (boot_verifier_set_observed(magic) != 0) {
    return -1;
}
if (boot_verifier_verify() != 0) {
    return -1;
}
```

### Runtime Initialization

Files: `src/shared/runtime.h`, `src/shared/runtime.c`

Purpose: provide one shared initialization/reset boundary for the harness.

Implemented APIs:

`int runtime_init(void)`

- Purpose: initializes the deterministic clock, message bus, watchdog, alert arbiter, shutdown state, and boot verifier.
- Parameters: none.
- Returns: `0` on success, `-1` if any subsystem initialization fails.
- Calling purpose: host app, simulator, or kernel startup boundary.
- Implementation detail: repeated `runtime_init()` calls return `0` if runtime is already initialized.

`void runtime_reset(void)`

- Purpose: resets bus, watchdog, alert arbiter, shutdown, boot verifier, and runtime initialized flag.
- Parameters: none.
- Returns: nothing.
- Calling purpose: tests or controlled reinitialization.

Safe startup example:

```c
if (runtime_init() != 0) {
    return -1;
}
```

### Suggestion Policy

Files: `src/shared/suggestion_policy.h`, `src/shared/suggestion_policy.c`

Purpose: make proactive suggestion timing, idle threshold, energy fallback, and anti-repeat behavior deterministic and host-testable.

Implemented struct:

```c
#define SUGGESTION_RECENT_CAPACITY 3

typedef struct {
    const char* entries[SUGGESTION_RECENT_CAPACITY];
    uint8_t next_index;
} SuggestionHistory;
```

Implemented APIs:

`uint8_t suggestion_policy_energy_for_hour(uint8_t hour)`

- Purpose: returns deterministic energy level for hour of day.
- Parameters: `hour`, hour value; implementation normalizes with `hour %= 24`.
- Returns: energy value.
- Calling purpose: model/user context update.

`int suggestion_policy_idle_fallback_minutes(uint8_t hour)`

- Purpose: returns deterministic fallback idle minutes when calendar idle time is unavailable/invalid.
- Parameters: `hour`, normalized with `hour %= 24`.
- Returns: fallback idle minutes.
- Calling purpose: suggestion evaluation.

`uint8_t suggestion_policy_should_check(uint8_t minute)`

- Purpose: decides if proactive suggestion logic may run at this minute.
- Parameters: `minute`, current minute.
- Returns: `1` for minute `0` or `30`, otherwise `0`.
- Calling purpose: guard before SNN inference.

`uint8_t suggestion_policy_should_suggest(int idle_minutes)`

- Purpose: checks idle threshold.
- Parameters: `idle_minutes`, computed idle time.
- Returns: `1` when `idle_minutes >= 30`, otherwise `0`.
- Calling purpose: guard before showing/adding suggestion.

`void suggestion_history_reset(SuggestionHistory* history)`

- Purpose: clears bounded recent-suggestion history.
- Parameters: `history`, pointer to history; null is ignored.
- Returns: nothing.
- Calling purpose: initialization/tests.

`uint8_t suggestion_history_contains(const SuggestionHistory* history, const char* suggestion)`

- Purpose: checks whether the exact suggestion pointer is already in recent history.
- Parameters: `history`, history pointer; `suggestion`, suggestion pointer.
- Returns: `1` if present, `0` if absent or inputs are null.
- Calling purpose: anti-repeat check.
- Implementation note: comparison is pointer equality, not string content comparison.

`void suggestion_history_record(SuggestionHistory* history, const char* suggestion)`

- Purpose: records suggestion into circular history.
- Parameters: `history`, history pointer; `suggestion`, suggestion pointer.
- Returns: nothing.
- Calling purpose: after a suggestion is accepted for display/scheduling.

Safe policy example:

```c
if (suggestion_policy_should_check(minute) != 0 &&
    suggestion_policy_should_suggest(idle_minutes) != 0) {
    // Call SNN inference or suggestion wrapper here.
}
```

### Dataset Contract

Files: `research/neuromorphic_assistant/use_case_data.py`, `tests/research/dataset_contract_test.py`

Purpose: protect the model/data interface from accidental changes.

Implemented constants:

```python
NUM_FEATURES = 16
NUM_CLASSES = len(SUGGESTION_LABELS)
```

Implemented APIs:

`generate_use_case_training_data(num_samples=NUM_SAMPLES, seed=42, noise_std=NOISE_STD)`

- Purpose: generates driving assistant training data.
- Parameters: `num_samples`, number of rows; `seed`, reproducibility seed; `noise_std`, Gaussian noise for continuous normalized features.
- Returns: `(X, y, scenarios)` where `X` is shape `(num_samples, 16)`, `y` is shape `(num_samples,)`, and `scenarios` is metadata.
- Calling purpose: training, smoke validation, dataset contract testing.

`get_splits(X, y, mode='70-20-10', seed=0)`

- Purpose: returns train/validation/test partitions.
- Parameters: `X`, features; `y`, labels; `mode`, either `'70-20-10'` or `'60-20-20'`; `seed`, shuffle seed.
- Returns: `X_train, X_val, X_test, y_train, y_val, y_test`.
- Calling purpose: training/validation workflows and tests.

`get_dataloaders(X, y, mode='70-20-10', batch_size=32, seed=0)`

- Purpose: wraps splits into PyTorch `DataLoader` objects.
- Parameters: dataset arrays, split mode, batch size, shuffle seed.
- Returns: train, validation, and test dataloaders.
- Calling purpose: model training scripts.

### Scheduler Policy

Files: `src/shared/scheduler_policy.h`, `src/shared/scheduler_policy.c`, `tests/host/scheduler_policy_test.c`

Status note: implemented in local integration work and included in the scheduler compliance target. It still needs normal branch handoff/push.

Purpose: separate deterministic scheduler decisions from low-level assembly/context switching.

Implemented definitions:

```c
#define SCHEDULER_POLICY_NO_TASK 0xFF

typedef enum {
    SCHEDULER_TASK_READY = 0,
    SCHEDULER_TASK_RUNNING = 1,
    SCHEDULER_TASK_SLEEPING = 2
} SchedulerTaskState;

typedef struct {
    uint8_t state;
    uint8_t priority;
    uint32_t wake_tick;
} SchedulerPolicyTask;
```

Implemented APIs:

`void scheduler_policy_init_task(SchedulerPolicyTask* task, uint8_t priority)`

- Purpose: initializes task state as ready with a priority and wake tick `0`.
- Parameters: `task`, task pointer; `priority`, lower numeric value means higher priority.
- Returns: nothing.
- Calling purpose: scheduler policy setup/tests.

`void scheduler_policy_sleep_current(SchedulerPolicyTask* task, uint32_t now_tick, uint32_t sleep_ticks)`

- Purpose: marks task sleeping until `now_tick + sleep_ticks`.
- Parameters: `task`, task pointer; `now_tick`, current tick; `sleep_ticks`, duration.
- Returns: nothing.
- Calling purpose: task sleep/yield policy.

`uint8_t scheduler_policy_wake_ready(SchedulerPolicyTask* tasks, uint8_t task_count, uint32_t now_tick)`

- Purpose: wakes sleeping tasks whose wake tick has arrived.
- Parameters: `tasks`, array; `task_count`, number of tasks; `now_tick`, current tick.
- Returns: number of tasks woken.
- Calling purpose: scheduler tick.
- Implementation detail: uses `(int32_t)(now_tick - wake_tick) >= 0` to support 32-bit wraparound.

`uint8_t scheduler_policy_select_ready(const SchedulerPolicyTask* tasks, uint8_t task_count, uint8_t idle_task)`

- Purpose: selects the ready task with the lowest numeric priority.
- Parameters: `tasks`, task array; `task_count`; `idle_task`, fallback index.
- Returns: selected task index or `SCHEDULER_POLICY_NO_TASK` if no ready task and idle index is invalid.
- Calling purpose: scheduler decision point.

## Confirmed Test Targets And Coverage

The following targets are present in the inspected Makefile from the local integration work.

### Message Bus Tests

- Command: `make message-bus-test`
- Tests: `test_init_idempotent`, `test_priority_order`, `test_low_overwrite`, `test_critical_capacity`, `test_clock_and_timestamp`, `test_trace_logging`.
- Coverage: init behavior, priority drain order, low-lane overwrite, critical overflow rejection, deterministic timestamping, trace logging.
- Result from prior validation log: passed.

### Watchdog And Alert Arbiter Tests

- Command: `make watchdog-alert-test`
- Tests: `test_watchdog_generates_alert`, `test_heartbeat_clears_alert_and_rearms`, `test_arbiter_leaves_non_alert_messages`.
- Coverage: missed heartbeat alerts, heartbeat recovery, alert sink dispatch, non-alert preservation.
- Result from prior validation log: passed.

### Shutdown Tests

- Command: `make shutdown-test`
- Tests: `test_flush_and_restore_round_trip`, `test_arbiter_routes_critical_alerts_to_shutdown`.
- Coverage: route/profile/media/log round trip, critical alerts captured through shutdown sink.
- Result from prior validation log: passed.

### Boot Verifier Tests

- Command: `make boot-verifier-test`
- Tests: `test_verifier_succeeds_on_marker_match`, `test_verifier_fails_on_marker_mismatch`.
- Coverage: matching marker success, mismatched marker failure, emitted boot verification messages.
- Result from prior validation log: passed.

### Runtime Tests

- Command: `make runtime-test`
- Test: `test_runtime_init_wires_subsystems`.
- Coverage: shared runtime initialization, zeroed clock baseline, available subsystem APIs.
- Result from prior validation log: passed.

### Suggestion Policy Tests

- Command: `make suggestion-policy-test`
- Coverage: deterministic energy, deterministic idle fallback, half-hour cadence, idle threshold, bounded anti-repeat history.
- Result from prior validation log: passed.

### Dataset Contract Tests

- Command: `make dataset-contract-test`
- Coverage: `NUM_FEATURES == 16`, `NUM_CLASSES == 12`, fixed-seed reproducibility, stable first row/labels/scenario metadata, 70-20-10 and 60-20-20 split sizes.
- Result from prior validation log: passed.

### Scheduler Policy Tests

- Command: `make scheduler-policy-test`
- Tests: `test_selects_lowest_numeric_priority`, `test_sleep_wakes_on_exact_tick`, `test_sleep_wakes_across_tick_wraparound`, `test_idle_fallback_when_no_task_ready`.
- Coverage: priority selection, exact wake tick, wraparound-safe waking, idle fallback.
- Result from prior validation log: passed.

### Compliance Test

- Command: `make compliance-test`
- Dependencies: `message-bus-test`, `watchdog-alert-test`, `shutdown-test`, `boot-verifier-test`, `runtime-test`, `suggestion-policy-test`, `scheduler-policy-test`, `python-research-compile`, `dataset-contract-test`.
- Coverage: host contracts, suggestion policy, scheduler policy, Python research syntax, dataset reproducibility.
- Result from prior validation log: passed.

### ISO Build Validation

- Command: `make iso-carplay`
- Coverage: CarPlay ISO build with scheduler object and shared suggestion policy object linked.
- Result from prior validation log: passed.
- Known warning: `ld: warning: build/multiboot_header.o: missing .note.GNU-stack section implies executable stack`.
- Note: this is build validation, not complete runtime validation of interrupts/UI behavior.

## Proposed Future Integration APIs

These APIs are proposed wrappers for Axel's kernel integration. They are not implemented unless explicitly listed in the implemented API sections above.

### Proposed Message Convenience Wrappers

Purpose: avoid repeated manual `Message` construction in kernel code.

```c
int minios_post_event(uint16_t type, uint32_t sender_id, const char* text);
int minios_post_alert(uint16_t type, uint32_t sender_id, const char* text);
int minios_post_critical(uint16_t type, uint32_t sender_id, const char* text);
```

Expected behavior if implemented:

- Build a bounded `Message` payload.
- Set priority based on wrapper name.
- Set `type` and `sender_id`.
- Leave `timestamp_ms = 0` so `message_bus_post()` applies deterministic time.
- Return `0` on success and nonzero on failure.

Safe example using proposed wrapper:

```c
if (minios_post_critical(MSG_TYPE_CRASH, ACTOR_KERNEL, "critical shutdown") != 0) {
    return -1;
}
```

### Proposed Actor IDs

Purpose: standardize `sender_id` values across kernel and harness code.

```c
#define ACTOR_KERNEL      1
#define ACTOR_UI          2
#define ACTOR_SNN         3
#define ACTOR_METRICS     4
#define ACTOR_SCHEDULER   5
#define ACTOR_WATCHDOG    6
#define ACTOR_SHUTDOWN    7
#define ACTOR_BOOT        8
```

Status: proposed only. The current code uses raw sender IDs in some places, such as boot verifier sender ID `1`.

### Proposed Suggestion Evaluation Wrapper

Purpose: keep kernel code from duplicating suggestion cadence, idle threshold, anti-repeat, and SNN inference boundary logic.

```c
typedef struct {
    uint8_t hour;
    uint8_t minute;
    uint8_t day_of_week;
    uint8_t energy_level;
    uint8_t engagement;
    int idle_minutes;
    uint8_t has_meeting;
    uint8_t accept_count;
    uint8_t reject_count;
} MiniOSSuggestionContext;

typedef struct {
    const char* text;
    uint8_t activity_id;
    uint8_t should_show;
} MiniOSSuggestionResult;

int minios_suggestion_evaluate(
    const MiniOSSuggestionContext* context,
    SuggestionHistory* history,
    MiniOSSuggestionResult* out
);
```

Expected behavior if implemented:

- Validate input pointers.
- Call `suggestion_policy_should_check(context->minute)`.
- Call `suggestion_policy_should_suggest(context->idle_minutes)`.
- Call the SNN inference boundary only if policy allows.
- Suppress repeats with `suggestion_history_contains()`.
- Record accepted/displayed suggestions with `suggestion_history_record()`.

Safe example:

```c
MiniOSSuggestionResult result = {0};

if (minios_suggestion_evaluate(&context, &history, &result) == 0 &&
    result.should_show != 0) {
    show_suggestion(result.text);
}
```

### Proposed Scheduler Kernel API

Purpose: prevent Axel's kernel code from depending on private task structs or assembly-specific layout.

```c
typedef uint8_t MiniOSTaskId;
typedef void (*MiniOSTaskEntry)(void);

int minios_scheduler_init(void);
int minios_task_register(
    const char* name,
    uint8_t priority,
    MiniOSTaskEntry entry,
    MiniOSTaskId* out_task_id
);
void minios_task_sleep(uint32_t ticks);
void minios_task_yield(void);
void minios_scheduler_tick(void);
MiniOSTaskId minios_scheduler_current_task(void);
int minios_scheduler_get_task_state(MiniOSTaskId task_id, SchedulerPolicyTask* out);
```

Expected behavior if implemented:

- `minios_scheduler_init()` initializes scheduler state and idle fallback.
- `minios_task_register()` registers task name, priority, entry point, and returns task ID.
- `minios_task_sleep()` puts current task to sleep for deterministic ticks.
- `minios_task_yield()` voluntarily gives up CPU.
- `minios_scheduler_tick()` advances ticks, wakes sleepers, and selects/switches tasks.
- `minios_scheduler_get_task_state()` exposes task state for diagnostics.

Safe setup example:

```c
MiniOSTaskId ui_task;

if (minios_scheduler_init() != 0) {
    return -1;
}
if (minios_task_register("ui", 0, task_ui, &ui_task) != 0) {
    return -1;
}
```

## Future Kernel Integration Guide

Suggested order for Axel integration:

1. Add `runtime_init()` at the kernel startup boundary.
2. Call `boot_verifier_set_expected()`, `boot_verifier_set_observed()`, and `boot_verifier_verify()` during boot.
3. Agree on final actor IDs and message type usage.
4. Use `message_bus_post()` or proposed message wrappers for kernel events.
5. Register kernel tasks with `watchdog_register()`.
6. Add `watchdog_heartbeat()` calls inside task loops.
7. Decide where `watchdog_tick()` and `alert_arbiter_process()` run.
8. Connect alert sinks for log, UI, and shutdown handling.
9. Update shutdown route/profile/media state through `shutdown_*` APIs.
10. Use `suggestion_policy_*` functions before SNN inference.
11. Add a narrow SNN inference wrapper rather than exposing research scripts to kernel code.
12. Decide whether scheduler policy is only a host-test contract or also the source of truth for kernel task state.
13. Run `make compliance-test` before handoff/merge.
14. Run `make iso-carplay` and then manual QEMU/runtime validation for interrupt/UI behavior.

## Open Decisions / Future Integration Questions

- Final actor ID assignments for kernel, UI, SNN, metrics, scheduler, watchdog, shutdown, and boot verifier.
- Final message type ID usage and whether current `MessageType` enum is sufficient.
- Which kernel tasks must be watchdog-monitored.
- What heartbeat intervals each task should use, noting the current watchdog alerts after `heartbeat_interval_ms * 2`.
- Where `watchdog_tick()` should run: scheduler tick, timer loop, or a dedicated health task.
- Where `alert_arbiter_process()` should run so alerts are routed without starving normal bus traffic.
- Which sinks Axel's kernel needs: log, UI, shutdown, or diagnostics.
- Shutdown persistence path in the kernel environment.
- Which route/profile/media fields Axel's code owns and when they should call shutdown setters.
- Final SNN inference boundary between research/model code and kernel code.
- Whether `SuggestionHistory` pointer equality is enough or whether string-content comparison is needed for future generated suggestions.
- Whether scheduler policy remains host-side validation only or becomes the kernel scheduling contract.
- Whether proposed scheduler task wrappers should be implemented before further kernel task work.
- How `make compliance-test` should be enforced before future merges.
- Whether full GPU training, QEMU boot, and hardware validation should be separate required gates.

## Summary

The deterministic harness now defines and tests core safety-related contracts for MiniOS: deterministic time, priority messaging, watchdog liveness, alert routing, shutdown persistence, boot verification, runtime initialization, suggestion policy, dataset reproducibility, and scheduler policy.

The important distinction for future work is this: the harness APIs listed under implemented API contracts exist in the code inspected from the integration work. The wrapper APIs listed under proposed future integration APIs are design suggestions for Axel's kernel integration and still need implementation if the team chooses to use them.

This gives the project a clearer path forward: keep testing deterministic contracts on the host, then connect Axel's kernel through small stable APIs instead of duplicating or bypassing the harness logic.
