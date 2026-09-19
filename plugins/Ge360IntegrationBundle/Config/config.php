<?php

declare(strict_types=1);

return [
    'name'        => 'GE360 Integration Hub',
    'description' => 'GE360 bridge for Prospex, SuiteCRM, n8n and Jarvis.',
    'version'     => '0.1.0',
    'author'      => 'GE360',
    'routes'      => [
        'main' => [
            'ge360_status' => [
                'path'       => '/ge360/status',
                'controller' => 'MauticPlugin\\Ge360IntegrationBundle\\Controller\\StatusController::indexAction',
                'methods'    => ['GET'],
            ],
        ],
    ],
    'menu' => [
        'main' => [
            'GE360' => [
                'route'     => 'ge360_status',
                'iconClass' => 'ri-radar-line',
                'priority'  => -10,
            ],
        ],
    ],
];
