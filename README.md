# devgateway.nginx

This is a low-level utility role to configure Nginx daemon *or* an individual site (`server` block
and related directives).

In a nutshell, this role translates YAML structures of certain grammar into Nginx grammar. Invoke
this role (which knows *how* to generate Nginx syntax) from a higher level role (which knows *what*
to generate). For example:

    - name: Configure a PHP site
      include_role:
        name: devgateway.nginx
        tasks_from: site
      vars:
        site:
          server: 
            include: fastcgi_params
            fastcgi_index: index.php
            server_name: "{{ server_name }}"
            listen: "{{ ssl | default(true) | ternary(443, 80) }}"
            ssl: "{{ ssl }}"

Thus, this role provides three independent modes:

* Daemon configuration which configures `nginx.conf` using `tasks_from: nginx`.

* Site configuration which configures `conf.d/`*`site`*`.conf` using `tasks_from: site`.

* SSL key pair installation and DH params generation.

## Role Grammar

The role grammar is based on [Nginx configuration
*contexts*](http://nginx.org/en/docs/beginners_guide.html#conf_structure). Site and daemon
configuration mode take just one dictionary each, which contains:

* Nginx directives applicable in current context and their values, as described below, and
* other contexts, potentially nested, with their directives and values.

**Be advised**, that although this role is idempotent, it operates on templates, and thus, on
entire files, not individual directives. If you manually add a directive to the target file, it
will be overwritten.

Dictionary members are expanded into Nginx directives, so that the key becomes the directive name,
and the value - its arguments. Directives, except blocks, are output in alphabetical order. Certain
key names are special, those are described below. The following rules are used for the values.

### Scalars

*   **Integers** are printed verbatim.

*   **Strings** get single-quoted if they contain spaces:

        auth_basic: You shall not pass

    becomes:

        auth_basic 'You shall not pass';

*   **Booleans** (except when in `upstream` or `map` blocks) become `on`/`off`:

        ssl: true

    becomes:

        ssl on;

### Lists

*   Simple **lists** become positional arguments, maintaining the given order:

        server_name:
          - bob.example.org
          - alice.example.org

    becomes:

        server_name bob.example.org alice.example.org;

*   However, if the first value of a **list** is also a list, only that child list is evaluated. It
yields multiple directives, with each value expanded as per these rules:

        fastcgi_hide_header:
          - - X-Drupal-Version
            - Debian: X-Dpkg
              RedHat: X-Rpm

    in Debian becomes:

        fastcgi_hide_header X-Drupal-Version;
        fastcgi_hide_header X-Dpkg;

### Dictionaries

*   If a **dictionary** contains special members `args` (list) or `kwargs` (dictionary), they
become positional and keyworded arguments, respectively. Keyworded arguments get sorted; positional
don't. Keyworded arguments that are lists, are joined using a colon:

        proxy_cache_path:
          args:
            - /var/cache/nginx/php
          kwargs:
            levels:
              - 1
              - 2
            keys_zone:
              - php
              - 40m
            inactive: 14d
            max_size: 512m

    becomes:

        proxy_cache_path /var/cache/nginx/php inactive=14d keys_zone=php:40m levels=1:2 max_size=512m;

*   If a **dictionary** contains a key which is the same as `ansible_os_family` value, then its
value is expanded further, according to these rules:

        ssl_certificate_key:
          Debian: /etc/ssl/private/snakeoil.pem
          RedHat: /etc/pki/tls/certs/snakeoil.pem

    in Debian becomes:

        ssl_certificate_key /etc/ssl/private/snakeoil.pem;

*   Otherwise, a **dictionary** expands to multiple directives, keys becoming the first positional
argument, and values expanded further as described above:

        access_log:
          /var/log/nginx/access.log: common
          /var/log/nginx/detailed.log:
            args:
              - longformat
            kwargs:
              gzip: 3
              flush: 1h

    becomes:

        access_log /var/log/nginx/access.log common;
        access_log /var/log/nginx/detailed.log longformat flush=1h gzip=3;

## Daemon Configuration Mode (`nginx.conf`)

This mode uses a dictionary called `ngx_settings`. All members are optional contexts:

* `main`
* `events`
* `http`

Example:

    ngx_settings:
      main:
        user:
          RedHat: nginx
          Debian: www-data
      events:
        worker_connections: 1024
      http:
        sendfile: true

### Optional Variable: `ngx_config_path`

Path to Nginx main configuration file. Its grammar will be verified with `nginx -tc`, so if you
include `conf.d` configs, run this mode *after* you configure all sites.

Default: `/etc/nginx/nginx.conf`

## Site Configuration Mode (`conf.d/`*`site`*`.conf`)

This mode uses a dictionary called `site`. The following members are special:

* `server` is the only required context. This will be referred to hereinafter as the main server.

* `redirect_from` is an optional list of `server_name`'s. If defined, it will yield a `server`
block with a redirect to the main server (two server blocks - SSL and plaintext, if the main server
uses SSL). See Redirect Servers below for details.

* Other recognized contexts are `http`, `maps`, and `upstreams`. Each is described below.

### `http` Context

These directives appear in the beginning of the file, and belong to the `http` context of Nginx
configuration, where the file is `include`'d.

### `maps` Context

This context is a list of dictionaries, each representing a [`map`
block](http://nginx.org/en/docs/http/ngx_http_map_module.html#map). The following members are
recognized in a dictionary:

* `hostnames` and `volatile` - booleans;
* `default` - scalar;
* `string` - the first argument of Nginx `map` directive, the string being evaluated;
* `var` - the second argument, dollar sign before the variable name may be omitted;
* `map` - dictionary, keys and values of the map.

Example:

    maps:
      - string: "$http_user_agent"
        var: compatible_browser
        default: 1
        map:
          "~MSIE": 0
          "~Lynx": 1

### `upstreams` Context

This context is a dictionary. Keys are upstream names, values are dictionaries of their directives.

Example:

    upstreams:
      backend:
        ip_hash: true
        server:
          - - localhost:9001
            - otherhost:9001

### Redirect Servers

Depending on the main server SSL settings, one or two (SSL-enabled and plaintext) extra `server`
blocks are generated. Each contains nothing but unconditional permanent redirect to the main
server. The logic of main server domain name detection is described below.

Additionally, if SSL is enabled for the main site, the third `server` block is generated, with the
same `server_name` as the main server. This block contains a permanent redirect from plaintext site
to SSL.

### Main Server Block

The main server block may contain an `ifs` member (a list of dictionaries), representing `if`
blocks. Each of those blocks must contain at least an `if` member - the conditional expression.

Example:

    server:
      ifs:
        - if: $http_referer ~ mallory\.example\.com
          return: 403

The main server block may also contain a `locations` member (also a list of dictionaries). Each of
those must contain at least a `location` member (which may also include matching operators like `~`
or `=`), and may contain nested `locations` members, as well as `ifs`.

Example:

    server:
      locations:
        - location: /scripts
          locations:
            - location: ~ \.php$
              fastcgi_pass: unix:/var/run/php

## Certificate/DH Mode

This mode uses at least two variables: `ngx_key` and `ngx_cert` which are the private key and the
certificate, respectively.

### Optional Variables

* `ngx_keypair_name` sets the base name (without extension) for the key and the certificate, and
defaults to *nginx*.

* `ngx_cert_chain` can be either a list of certificates in the chain (from intermediate to root
CA), or a string with the said chain prebuilt.

* `ngx_dhparam_bits` is the length of DH parameter to generated, default is 2048.

* `ngx_key_dir`, `ngx_cert_dir`, and `ngx_dhparam_path` are dictionaries with `ansible_os_family`
as keys, and define default directories and filename for the above.

Playbook example:

    - hosts: webservers
      tasks:
        - name: Install key pair
          import_role:
            name: devgateway.nginx
            tasks_from: certificate
          vars:
            ngx_keypair_name: snakeoil
            ngx_key: |-
              -----BEGIN RSA PRIVATE KEY-----
              My private key
              -----END RSA PRIVATE KEY-----
            ngx_cert: |-
              -----BEGIN CERTIFICATE-----
              My certificate
              -----END CERTIFICATE-----
            ngx_cert_chain:
              - |-
                -----BEGIN CERTIFICATE-----
                Intermediate vendor
                -----END CERTIFICATE-----
              - |-
                -----BEGIN CERTIFICATE-----
                Root CA
                -----END CERTIFICATE-----
