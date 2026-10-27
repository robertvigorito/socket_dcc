# API reference

API documentation is generated from the modules in `src/socket_dcc/`. The `socket_dcc` package
contains the application client/server and interface; its CLI and modular GUI are subpackages. Nuke
startup hooks live separately under `src/nuke/` and are not part of this Python API.

## Core package

::: socket_dcc.client
    options:
      show_root_heading: true
      members: true

::: socket_dcc.defaults
    options:
      show_root_heading: true
      members: true

::: socket_dcc.interface
    options:
      show_root_heading: true
      members: true

::: socket_dcc.server
    options:
      show_root_heading: true
      members: true

## Command-line interface

The CLI entry point is `socket_dcc.cli.initiate`; individual commands are implemented in the modules
listed below.

::: socket_dcc.cli.initiate
    options:
      show_root_heading: true
      members: true

::: socket_dcc.cli.code
    options:
      show_root_heading: true
      members: true

::: socket_dcc.cli.common
    options:
      show_root_heading: true
      members: true

::: socket_dcc.cli.configure
    options:
      show_root_heading: true
      members: true

::: socket_dcc.cli.generate_token
    options:
      show_root_heading: true
      members: true

::: socket_dcc.cli.info
    options:
      show_root_heading: true
      members: true

::: socket_dcc.cli.path
    options:
      show_root_heading: true
      members: true

::: socket_dcc.cli.show
    options:
      show_root_heading: true
      members: true

::: socket_dcc.cli.test
    options:
      show_root_heading: true
      members: true

::: socket_dcc.cli.test_raise
    options:
      show_root_heading: true
      members: true

## GUI

::: socket_dcc.core.gui
    options:
      show_root_heading: true
      members: true

::: socket_dcc.core.gui.layout
    options:
      show_root_heading: true
      members: true

::: socket_dcc.core.gui.signals
    options:
      show_root_heading: true
      members: true

::: socket_dcc.core.gui.utils
    options:
      show_root_heading: true
      members: true

::: socket_dcc.core.gui.window
    options:
      show_root_heading: true
      members: true
