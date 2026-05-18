---
title: "Integrations"
date: 2026-05-18
focus: tech
---

# Integrations

## External APIs

None detected. This is a local asset parsing tool, not a networked application.

## Databases

None.

## Auth Providers

None.

## Engine Integrations

- **Unreal Engine Asset Pipeline** — The tool interfaces with UE's `.uasset` binary format
  - `FLinkerLoad` — UE's internal linker for loading .uasset packages
  - `UPackage` — Asset container corresponding to a .uasset file
  - `UBlueprintGeneratedClass` — UClass generated from Blueprint assets

## File I/O

- Reads `.uasset` binary files from disk
- Test file: `BP_FirstPersonCharacter.uasset` (56KB)
