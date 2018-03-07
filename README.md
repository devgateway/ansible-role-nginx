# devgateway.nginx

This is a low-level utility role to configure Nginx daemon *or* an individual site (`server` block and related directives).

In a nutshell, this role translates YAML structures of certain grammar into Nginx grammar. Invoke this role (which knows *how* to generate Nginx syntax) from a higher level role (which knows *what* to generate). For example:

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

Thus, this role provides two independent modes:

* daemon configuration which configures `nginx.conf` using `tasks_from: nginx`, and
* site configuration which configures `conf.d/`*`site`*`.conf` using `tasks_from: site`.

These two are shipped in a single role, because they share a Jinja2 macro library for Nginx grammar.

The role grammar is based on [Nginx configuration *contexts*](http://nginx.org/en/docs/beginners_guide.html#conf_structure). Either mode takes just one dictionary, which contains:

* Nginx directives applicable in current context and their values, as described below, and
* other contexts, potentially nested, with their directives and values.

**Be advised**, that although this role is idempotent, it operates on templates, and thus, on entire files, not individual directives. If you manually add a directive to the target file, it will be overwritten.

## Role Grammar

Dictionary members are expanded into Nginx directives, so that the key becomes the directive name, and the value - its arguments. Directives, except blocks, are output in alphabetical order. Certain key names are special, those are described below. The following rules are used for the values.

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

*   However, if the first value of the **list** is also a list, only that one is evaluated. It yields multiple directives, with each value expanded as per these rules:

        fastcgi_hide_header:
          - - X-Drupal-Version
            - Debian: X-Dpkg
              RedHat: X-Rpm

    in Debian becomes:

        fastcgi_hide_header X-Drupal-Version;
        fastcgi_hide_header X-Dpkg;

### Dictionaries

*   If a **dictionary** contains special members `args` (list) or `kwargs` (dictionary), they become positional and keyworded arguments, respectively. Keyworded arguments get sorted; positional don't. Keyworded arguments that are lists, are joined using a colon:

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

*   If the **dictionary** contains a key which is the same as `ansible_os_family` value, then its value is expanded further, according to these rules:

        ssl_certificate_key:
          Debian: /etc/ssl/private/snakeoil.pem
          RedHat: /etc/pki/tls/certs/snakeoil.pem

    in Debian becomes:

        ssl_certificate_key /etc/ssl/private/snakeoil.pem;

*   Otherwise, the **dictionary** expands to multiple directives, keys becoming the first positional argument, and values expanded further as described above:

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

### Optional Variable: `ngx_config_path`

Path to Nginx main configuration file. Its grammar will be verified with `nginx -tc`, so if you include `conf.d` configs, run this mode *after* you configure each site.

Default: `/etc/nginx/nginx.conf`

## Site Configuration Mode (`conf.d/`*`site`*`.conf`)

This mode uses a dictionary called `site`. The following members are special:

* `server` is the only required context. This will be referred to hereinafter as the main server.

* `redirect_from` is an optional list of `server_name`'s. Each will yield a `server` block with a redirect to the main server. See Redirect Servers below for details.

* Other recognized contexts are `http`, `maps`, and `upstreams`. Each is described below.

### `http` Context

These directives appear in the beginning of the file, and belong to the `http` context of Nginx configuration, where the file is `include`'d.

### `maps` Context

This context is a list of dictionaries, each representing a [`map` block](http://nginx.org/en/docs/http/ngx_http_map_module.html#map). The following members are recognized in a dictionary:

* `hostnames` and `volatile` - booleans;
* `default` - scalar;
* `string` - the first argument of Nginx `map` directive, the string being evaluated;
* `var` - the second argument, dollar sign before the variable name may be omitted;
* `map` - dictionary, keys and values of the map.

### `upstreams` Context

This context is a dictionary. Keys are upstream names, values are dictionaries of their directives.
