---
title: "Conventions"
date: 2026-05-18
focus: quality
---

# Conventions

## Language

- **Documentation**: Chinese (as specified in CLAUDE.md)
- **Code**: English (standard UE C++ conventions)

## C++ Conventions (from reference class)

- **UE naming**: `A` prefix for Actor classes, `U` prefix for UObject classes, `F` prefix for structs
- **UPROPERTY macros**: `VisibleAnywhere`, `BlueprintReadOnly`, `EditAnywhere` with category metadata
- **UFUNCTION macros**: `BlueprintCallable` with category
- **Header guards**: `#pragma once`
- **Include order**: `CoreMinimal.h` → framework headers → generated header

## Blueprint Conventions (from reference docs)

- **Node format**: `Begin Object ... End Object` blocks
- **Fields**: Class, Name, ExportPath, FunctionReference, NodeGuid
- **Pins**: `CustomProperties Pin` with PinId/PinName/PinType/LinkedTo/Direction
- **Coordinates**: NodePosX/NodePosY for canvas position

## File Organization

- Reference docs use Chinese filenames
- Test assets use `BP_` prefix
- `temp/` directory for cache and temporary files (gitignored)

## Git

- Newly initialized repository
- No commit history yet
