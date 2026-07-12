---
type: Reference
title: "Connectors: curated reference"
description: "A baseline map of common systems to their UiPath implementation, used to inform the per-step UI / API / connector decision during brainstorm; defer to the installed uipath-platform skill for current specifics."
timestamp: 2026-06-08
tags: [rpa, reference]
---

# Connectors: curated reference

A baseline map of common systems to their UiPath implementation, used to **inform** the per-step
"UI / API / connector?" question during brainstorm, neutrally, not to force API everywhere. For anything
not listed, or for specifics (current connector names, scopes, activities), **defer to the installed
`uipath-platform` skill** (Integration Service is the source of truth and changes over time).

## Decision ladder (per step, pick the highest that fits)

1. **Integration Service connector** activity, if a maintained connector exists for the system.
2. **Vendor API** via HTTP Request, if there's a documented API but no connector (see `.wit/inputs.md` API
   refs).
3. **Official UiPath activity package**: Mail, Excel, Word, PDF, Database, etc.
4. **UI automation**, when none of the above exist or the interaction is inherently UI. A valid choice;
   flag it in the SDD as higher-maintenance/selector-dependent.

## Common systems (baseline; verify specifics with uipath-platform)

| System | Preferred implementation | Auth |
|--------|--------------------------|------|
| Outlook / Exchange / Teams / SharePoint / OneDrive | Microsoft 365 connector (Graph) | OAuth / app reg |
| Excel / CSV (local) | Excel / Workbook activities | n/a |
| Salesforce | Salesforce connector | OAuth |
| ServiceNow | ServiceNow connector | OAuth / basic |
| SAP | SAP connector / SAP GUI (UI) when no API | SAP creds |
| Databases (SQL Server, Oracle, Postgres) | Database activities (ODBC/connection string) | conn string asset |
| Generic REST/SOAP | HTTP Request / SOAP activities | per API |
| Google Workspace (Gmail, Sheets, Drive) | Google Workspace connector | OAuth |
| Jira / Confluence | Atlassian connector | OAuth / token |
| DocuSign, Workday, NetSuite, Slack | respective Integration Service connectors | OAuth |
| Legacy desktop / Citrix / mainframe | UI automation (Computer Vision for Citrix) | app creds |

Notes:
- Prefer connectors/APIs for **maintainability** (selectors break; APIs are stable), but only when one
  genuinely exists. Record the choice + rationale inline in `tobe.md` and in sdd:6.
- Credentials/secrets always become Orchestrator **assets/credentials** (names in the SDD), never
  hardcoded.
- Keep this list short and current-ish; it's a prompt, not an inventory. `uipath-platform` has the real,
  up-to-date connector catalog.
