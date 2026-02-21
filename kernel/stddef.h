/* stddef.h - Standard definitions for freestanding kernel */

#ifndef _STDDEF_H
#define _STDDEF_H

/* size_t - unsigned integer type for sizes */
typedef unsigned long size_t;

/* ptrdiff_t - signed integer type for pointer differences */
typedef long ptrdiff_t;

/* NULL pointer constant */
#define NULL ((void*)0)

/* offsetof macro - offset of a member in a structure */
#define offsetof(type, member) ((size_t)&((type*)0)->member)

#endif /* _STDDEF_H */
