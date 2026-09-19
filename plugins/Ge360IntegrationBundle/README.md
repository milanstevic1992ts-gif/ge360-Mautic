# GE360 Integration Hub

A deliberately small Mautic plugin that exposes GE360 integration status without modifying Mautic core files.

Current functions:

- registers the GE360 plugin in Mautic;
- adds a private `/ge360/status` route;
- detects configuration for Prospex, SuiteCRM, n8n, Jarvis and the GE360 Bridge;
- never returns endpoint URLs, tokens or passwords.

The actual workflow orchestration stays in n8n/GE360 so Mautic remains upgradeable.
