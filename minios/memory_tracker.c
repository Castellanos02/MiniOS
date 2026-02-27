// memory_tracker.c - Comprehensive memory change tracking system
// Records all memory state changes, patterns, and analytics

#include <stdint.h>
#include <stddef.h>

// ============================================================================
// MEMORY TRACKING CONFIGURATION
// ============================================================================

#define MAX_MEMORY_EVENTS 1000      // Circular buffer size
#define MAX_MEMORY_REGIONS 50       // Track up to 50 regions
#define MEMORY_SNAPSHOT_INTERVAL 100 // Snapshots every 100 events

// ============================================================================
// MEMORY EVENT TYPES
// ============================================================================

typedef enum {
    MEM_EVENT_ALLOC = 0,      // Memory allocated
    MEM_EVENT_FREE,           // Memory freed
    MEM_EVENT_WRITE,          // Memory written
    MEM_EVENT_READ,           // Memory read
    MEM_EVENT_MODIFY,         // Memory modified
    MEM_EVENT_COPY,           // Memory copied
    MEM_EVENT_ZERO,           // Memory zeroed
    MEM_EVENT_STACK_PUSH,     // Stack growth
    MEM_EVENT_STACK_POP,      // Stack shrinkage
    MEM_EVENT_HEAP_GROW,      // Heap expansion
    MEM_EVENT_HEAP_SHRINK,    // Heap contraction
    MEM_EVENT_PAGE_FAULT,     // Page fault occurred
    MEM_EVENT_CACHE_HIT,      // Cache hit
    MEM_EVENT_CACHE_MISS      // Cache miss
} MemoryEventType;

// Memory event record
typedef struct {
    MemoryEventType type;
    uint64_t timestamp;         // Cycle counter
    void* address;              // Memory address
    size_t size;                // Size in bytes
    uint32_t sequence_num;      // Sequential event number
    uint8_t source;             // 0=kernel, 1=user, 2=system
    uint8_t flags;              // Additional flags
} MemoryEvent;

// Memory region descriptor
typedef struct {
    void* start_addr;
    void* end_addr;
    size_t size;
    uint32_t allocation_time;
    uint32_t last_access_time;
    uint32_t access_count;
    uint8_t type;               // 0=stack, 1=heap, 2=static, 3=code
    uint8_t protection;         // r/w/x flags
    char name[32];              // Region name
} MemoryRegion;

// Memory snapshot (state at a point in time)
typedef struct {
    uint64_t timestamp;
    uint32_t total_allocated;
    uint32_t total_freed;
    uint32_t active_regions;
    uint32_t stack_size;
    uint32_t heap_size;
    uint32_t fragmentation;     // Percentage
    uint32_t event_count;
} MemorySnapshot;

// Memory statistics
typedef struct {
    uint64_t total_allocs;
    uint64_t total_frees;
    uint64_t total_reads;
    uint64_t total_writes;
    uint64_t bytes_allocated;
    uint64_t bytes_freed;
    uint64_t peak_memory_usage;
    uint64_t current_memory_usage;
    uint32_t alloc_failures;
    uint32_t double_frees;
    uint32_t memory_leaks;
    float avg_allocation_size;
    float fragmentation_ratio;
} MemoryStatistics;

// ============================================================================
// GLOBAL MEMORY TRACKING STATE
// ============================================================================

static struct {
    MemoryEvent events[MAX_MEMORY_EVENTS];
    uint32_t event_head;           // Next write position
    uint32_t event_tail;           // Oldest event
    uint32_t event_sequence;       // Global sequence counter
    
    MemoryRegion regions[MAX_MEMORY_REGIONS];
    uint32_t region_count;
    
    MemorySnapshot snapshots[100];
    uint32_t snapshot_count;
    
    MemoryStatistics stats;
    
    uint64_t cycle_counter;        // Timestamp source
    uint8_t tracking_enabled;
} g_mem_tracker = {0};

// ============================================================================
// CORE TRACKING FUNCTIONS
// ============================================================================

// Initialize memory tracker
void mem_tracker_init(void) {
    for (uint32_t i = 0; i < MAX_MEMORY_EVENTS; i++) {
        g_mem_tracker.events[i].type = 0;
        g_mem_tracker.events[i].timestamp = 0;
        g_mem_tracker.events[i].address = NULL;
        g_mem_tracker.events[i].size = 0;
    }
    
    g_mem_tracker.event_head = 0;
    g_mem_tracker.event_tail = 0;
    g_mem_tracker.event_sequence = 0;
    g_mem_tracker.region_count = 0;
    g_mem_tracker.snapshot_count = 0;
    g_mem_tracker.cycle_counter = 0;
    g_mem_tracker.tracking_enabled = 1;
    
    // Initialize statistics
    g_mem_tracker.stats.total_allocs = 0;
    g_mem_tracker.stats.total_frees = 0;
    g_mem_tracker.stats.bytes_allocated = 0;
    g_mem_tracker.stats.bytes_freed = 0;
    g_mem_tracker.stats.current_memory_usage = 0;
    g_mem_tracker.stats.peak_memory_usage = 0;
}

// Record a memory event
void mem_track_event(MemoryEventType type, void* addr, size_t size, uint8_t source) {
    if (!g_mem_tracker.tracking_enabled) return;
    
    // Create event
    MemoryEvent* event = &g_mem_tracker.events[g_mem_tracker.event_head];
    event->type = type;
    event->timestamp = g_mem_tracker.cycle_counter;
    event->address = addr;
    event->size = size;
    event->sequence_num = g_mem_tracker.event_sequence++;
    event->source = source;
    event->flags = 0;
    
    // Advance head (circular buffer)
    g_mem_tracker.event_head = (g_mem_tracker.event_head + 1) % MAX_MEMORY_EVENTS;
    
    // If we've wrapped around, advance tail
    if (g_mem_tracker.event_head == g_mem_tracker.event_tail) {
        g_mem_tracker.event_tail = (g_mem_tracker.event_tail + 1) % MAX_MEMORY_EVENTS;
    }
    
    // Update statistics
    switch (type) {
        case MEM_EVENT_ALLOC:
            g_mem_tracker.stats.total_allocs++;
            g_mem_tracker.stats.bytes_allocated += size;
            g_mem_tracker.stats.current_memory_usage += size;
            if (g_mem_tracker.stats.current_memory_usage > g_mem_tracker.stats.peak_memory_usage) {
                g_mem_tracker.stats.peak_memory_usage = g_mem_tracker.stats.current_memory_usage;
            }
            break;
            
        case MEM_EVENT_FREE:
            g_mem_tracker.stats.total_frees++;
            g_mem_tracker.stats.bytes_freed += size;
            if (g_mem_tracker.stats.current_memory_usage >= size) {
                g_mem_tracker.stats.current_memory_usage -= size;
            }
            break;
            
        case MEM_EVENT_READ:
            g_mem_tracker.stats.total_reads++;
            break;
            
        case MEM_EVENT_WRITE:
            g_mem_tracker.stats.total_writes++;
            break;
            
        default:
            break;
    }
    
    // Update average allocation size
    if (g_mem_tracker.stats.total_allocs > 0) {
        g_mem_tracker.stats.avg_allocation_size = 
            (float)g_mem_tracker.stats.bytes_allocated / g_mem_tracker.stats.total_allocs;
    }
    
    // Take snapshot periodically
    if (g_mem_tracker.event_sequence % MEMORY_SNAPSHOT_INTERVAL == 0) {
        mem_take_snapshot();
    }
}

// Register a memory region
uint32_t mem_register_region(void* start, size_t size, uint8_t type, const char* name) {
    if (g_mem_tracker.region_count >= MAX_MEMORY_REGIONS) {
        return 0xFFFFFFFF; // Failed
    }
    
    MemoryRegion* region = &g_mem_tracker.regions[g_mem_tracker.region_count];
    region->start_addr = start;
    region->end_addr = (void*)((uintptr_t)start + size);
    region->size = size;
    region->allocation_time = (uint32_t)g_mem_tracker.cycle_counter;
    region->last_access_time = (uint32_t)g_mem_tracker.cycle_counter;
    region->access_count = 0;
    region->type = type;
    region->protection = 0x7; // rwx by default
    
    // Copy name (simple copy, no strncpy in kernel)
    for (int i = 0; i < 31 && name[i]; i++) {
        region->name[i] = name[i];
    }
    region->name[31] = '\0';
    
    return g_mem_tracker.region_count++;
}

// Take a memory snapshot
void mem_take_snapshot(void) {
    if (g_mem_tracker.snapshot_count >= 100) {
        // Circular overwrite
        g_mem_tracker.snapshot_count = 0;
    }
    
    MemorySnapshot* snap = &g_mem_tracker.snapshots[g_mem_tracker.snapshot_count++];
    snap->timestamp = g_mem_tracker.cycle_counter;
    snap->total_allocated = (uint32_t)g_mem_tracker.stats.bytes_allocated;
    snap->total_freed = (uint32_t)g_mem_tracker.stats.bytes_freed;
    snap->active_regions = g_mem_tracker.region_count;
    snap->event_count = g_mem_tracker.event_sequence;
    
    // Calculate fragmentation (simplified)
    if (g_mem_tracker.stats.current_memory_usage > 0) {
        snap->fragmentation = (uint32_t)(
            ((float)(g_mem_tracker.stats.total_allocs - g_mem_tracker.stats.total_frees) / 
             g_mem_tracker.stats.total_allocs) * 100.0f
        );
    } else {
        snap->fragmentation = 0;
    }
}

// Update cycle counter (called frequently)
void mem_tick(uint32_t cycles) {
    g_mem_tracker.cycle_counter += cycles;
}

// ============================================================================
// MEMORY PATTERN ANALYSIS
// ============================================================================

// Detect memory patterns
typedef struct {
    uint8_t has_leak;              // Memory leak detected
    uint8_t has_fragmentation;     // High fragmentation
    uint8_t has_thrashing;         // Excessive alloc/free
    uint32_t leak_bytes;           // Estimated leaked bytes
    float access_locality;         // 0.0-1.0 (temporal locality)
} MemoryPatterns;

MemoryPatterns mem_analyze_patterns(void) {
    MemoryPatterns patterns = {0};
    
    // Detect leaks: more allocs than frees
    if (g_mem_tracker.stats.total_allocs > g_mem_tracker.stats.total_frees + 10) {
        patterns.has_leak = 1;
        patterns.leak_bytes = (uint32_t)(
            g_mem_tracker.stats.bytes_allocated - g_mem_tracker.stats.bytes_freed
        );
    }
    
    // Detect fragmentation
    if (g_mem_tracker.stats.fragmentation_ratio > 0.3f) {
        patterns.has_fragmentation = 1;
    }
    
    // Detect thrashing: high alloc/free rate
    if (g_mem_tracker.stats.total_allocs > 1000 && 
        g_mem_tracker.stats.total_frees > 1000) {
        float alloc_free_ratio = (float)g_mem_tracker.stats.total_frees / 
                                 g_mem_tracker.stats.total_allocs;
        if (alloc_free_ratio > 0.9f) {
            patterns.has_thrashing = 1;
        }
    }
    
    return patterns;
}

// ============================================================================
// QUERY & REPORTING
// ============================================================================

// Get current memory statistics
MemoryStatistics mem_get_stats(void) {
    return g_mem_tracker.stats;
}

// Get recent memory events (last N events)
uint32_t mem_get_recent_events(MemoryEvent* buffer, uint32_t max_events) {
    uint32_t count = 0;
    uint32_t pos = g_mem_tracker.event_head;
    
    // Walk backwards from head
    while (count < max_events && pos != g_mem_tracker.event_tail) {
        // Move backwards (circular)
        if (pos == 0) {
            pos = MAX_MEMORY_EVENTS - 1;
        } else {
            pos--;
        }
        
        buffer[count++] = g_mem_tracker.events[pos];
    }
    
    return count;
}

// Get memory regions
uint32_t mem_get_regions(MemoryRegion* buffer, uint32_t max_regions) {
    uint32_t count = g_mem_tracker.region_count;
    if (count > max_regions) {
        count = max_regions;
    }
    
    for (uint32_t i = 0; i < count; i++) {
        buffer[i] = g_mem_tracker.regions[i];
    }
    
    return count;
}

// Get memory usage percentage
uint8_t mem_get_usage_percent(void) {
    // This would need total system memory
    // For now, just return a scaled value
    if (g_mem_tracker.stats.peak_memory_usage == 0) return 0;
    
    return (uint8_t)((g_mem_tracker.stats.current_memory_usage * 100) / 
                     g_mem_tracker.stats.peak_memory_usage);
}

// ============================================================================
// EXPORT & LOGGING
// ============================================================================

// Format memory event as string
void mem_event_to_string(const MemoryEvent* event, char* buffer, size_t size) {
    const char* type_names[] = {
        "ALLOC", "FREE", "WRITE", "READ", "MODIFY", "COPY", "ZERO",
        "STACK+", "STACK-", "HEAP+", "HEAP-", "PGFAULT", "CACHE+", "CACHE-"
    };
    
    // Simple formatting (no snprintf)
    // Format: "TYPE addr=0x... size=... seq=..."
    // Implementation would build this string
    buffer[0] = '\0';
}

// Export memory log to buffer
uint32_t mem_export_log(char* buffer, size_t buffer_size) {
    // Would format all events as text
    // Return bytes written
    return 0;
}
