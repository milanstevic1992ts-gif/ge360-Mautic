<?php

declare(strict_types=1);

namespace MauticPlugin\Ge360IntegrationBundle\Service;

final class ConnectionRegistry
{
    private const SERVICES = [
        'prospex'  => 'GE360_PROSPEX_URL',
        'suitecrm' => 'GE360_SUITECRM_URL',
        'n8n'      => 'GE360_N8N_URL',
        'jarvis'   => 'GE360_JARVIS_URL',
        'bridge'   => 'GE360_BRIDGE_URL',
    ];

    /**
     * Return configuration state only; never expose endpoint URLs or secrets.
     *
     * @return array<string, bool>
     */
    public static function configured(): array
    {
        $status = [];

        foreach (self::SERVICES as $name => $environmentVariable) {
            $value = getenv($environmentVariable);
            $status[$name] = false !== $value && '' !== trim((string) $value);
        }

        return $status;
    }
}
