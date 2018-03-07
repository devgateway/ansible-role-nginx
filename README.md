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

Dictionary members are expanded into Nginx directives, so that the key becomes the directive name, and the value - its arguments. Directives, except blocks, are output in alphabetical order. The following rules are used for the values:

*   **Integers** are printed verbatim.

*   **Strings** get single-quoted if they contain spaces:

        auth_basic: You shall not pass

    becomes:

        auth_basic 'You shall not pass';

*   **Booleans** (except when in `upstream` or `map` blocks) become `on`/`off`:

        ssl: true

    becomes:

        ssl on;

*   Simple **lists** become positional arguments, maintaining the given order:

        server_name:
          - bob.example.org
          - alice.example.org

    becomes:

        server_name bob.example.org alice.example.org;

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
