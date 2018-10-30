s/[[:space:]]*#.*//
s/{[[:space:]]*\([^[:space:]]\)/{\n\1/
s/;[[:space:]]*\([^[:space:]]\)/;\n\1/
s/\([^{[:space:]]\)[[:space:]]*}/\1;\n}/
