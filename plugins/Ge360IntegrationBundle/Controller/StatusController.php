<?php

declare(strict_types=1);

namespace MauticPlugin\Ge360IntegrationBundle\Controller;

use MauticPlugin\Ge360IntegrationBundle\Service\ConnectionRegistry;
use Symfony\Component\HttpFoundation\JsonResponse;

final class StatusController
{
    public function indexAction(): JsonResponse
    {
        return new JsonResponse([
            'product'      => 'GE360 Mautic',
            'plugin'       => 'Ge360IntegrationBundle',
            'version'      => '0.1.0',
            'status'       => 'ok',
            'integrations' => ConnectionRegistry::configured(),
        ]);
    }
}
