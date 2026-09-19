ARG MAUTIC_IMAGE=mautic/mautic:7.2-apache
FROM ${MAUTIC_IMAGE}

USER root
COPY --chown=www-data:www-data plugins/Ge360IntegrationBundle /var/www/html/docroot/plugins/Ge360IntegrationBundle
USER www-data
