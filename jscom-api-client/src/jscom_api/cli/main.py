"""CLI application for jscom-api."""

import json
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from jscom_api import JscomApiClient, __version__, load_config
from jscom_api.exceptions import (
    AuthenticationError,
    JscomApiError,
    NetworkError,
    ServerError,
    ValidationError,
)

app = typer.Typer(
    help="CLI for jscom-mini-services API",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode=None,
)
dns_app = typer.Typer(help="DNS management commands", rich_markup_mode=None)
app.add_typer(dns_app, name="dns")

console = Console()
err_console = Console(stderr=True)


class State:
    """Global state for CLI options."""

    base_url: str | None = None
    token: str | None = None


state = State()


@app.callback()
def main(
    base_url: Annotated[
        str | None,
        typer.Option(
            "--base-url",
            help="API base URL (overrides JSCOM_API_BASE_URL env var)",
        ),
    ] = None,
    token: Annotated[
        str | None,
        typer.Option(
            "--token",
            help="Authentication token (overrides JSCOM_API_TOKEN env var)",
        ),
    ] = None,
) -> None:
    """Global options for jscom-api CLI."""
    state.base_url = base_url
    state.token = token


@app.command()
def version() -> None:
    """Show version and exit."""
    console.print(f"jscom-api version {__version__}")
    raise typer.Exit()


@app.command()
def ip(
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output as JSON",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Output only the IP address",
        ),
    ] = False,
) -> None:
    """Get your public IP address.

    Examples:
        jscom-api ip                    # Human-readable output
        jscom-api ip --json             # JSON output
        jscom-api ip --quiet            # Just the IP, nothing else
    """
    try:
        config = load_config(
            base_url=state.base_url,
            auth_token=state.token,
        )

        with JscomApiClient(
            base_url=config.base_url,
            auth_token=config.auth_token,
            timeout=config.timeout,
        ) as client:
            result = client.get_my_ip()

            if quiet:
                console.print(result.ip)
            elif json_output:
                console.print_json(json.dumps({"ip": result.ip}))
            else:
                table = Table(show_header=True, header_style="bold cyan")
                table.add_column("Your Public IP", style="green")
                table.add_row(result.ip)
                console.print(table)

    except NetworkError as e:
        err_console.print(f"[red]Network error:[/red] {e}")
        raise typer.Exit(code=1) from None
    except ServerError as e:
        err_console.print(f"[red]Server error:[/red] {e}")
        raise typer.Exit(code=1) from None
    except JscomApiError as e:
        err_console.print(f"[red]API error:[/red] {e}")
        raise typer.Exit(code=1) from None
    except Exception as e:
        err_console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(code=1) from None


@dns_app.command("update")
def dns_update(
    domain: Annotated[
        str,
        typer.Option(
            "--domain",
            help="Domain name to update (must include trailing dot, e.g., 'mc.example.com.')",
        ),
    ],
    ip_address: Annotated[
        str | None,
        typer.Option(
            "--ip",
            help="IP address to set",
        ),
    ] = None,
    use_current_ip: Annotated[
        bool,
        typer.Option(
            "--use-current-ip",
            help="Auto-fetch and use current public IP",
        ),
    ] = False,
) -> None:
    """Update a DNS A record.

    Either --ip or --use-current-ip must be provided (but not both).

    Examples:
        jscom-api dns update --domain minecraft.johnsosoka.com. --ip 1.2.3.4
        jscom-api dns update --domain minecraft.johnsosoka.com. --use-current-ip
    """
    # Validate mutually exclusive options
    if ip_address and use_current_ip:
        err_console.print(
            "[red]Error:[/red] --ip and --use-current-ip are mutually exclusive. "
            "Provide one or the other."
        )
        raise typer.Exit(code=1) from None

    if not ip_address and not use_current_ip:
        err_console.print(
            "[red]Error:[/red] Either --ip or --use-current-ip must be provided."
        )
        raise typer.Exit(code=1) from None

    try:
        config = load_config(
            base_url=state.base_url,
            auth_token=state.token,
        )

        with JscomApiClient(
            base_url=config.base_url,
            auth_token=config.auth_token,
            timeout=config.timeout,
        ) as client:
            # Fetch current IP if requested
            target_ip = ip_address
            if use_current_ip:
                console.print("[cyan]Fetching current public IP...[/cyan]")
                ip_result = client.get_my_ip()
                target_ip = ip_result.ip
                console.print(f"[cyan]Current IP:[/cyan] {target_ip}")

            # Validate we have an IP at this point (should always be true)
            if not target_ip:
                err_console.print("[red]Error:[/red] No IP address available")
                raise typer.Exit(code=1) from None

            # Update DNS record
            console.print(f"[cyan]Updating DNS record for {domain}...[/cyan]")
            result = client.update_dns(domain=domain, ip=target_ip)

            # Display success
            console.print(f"[green]Success![/green] {result.message}")
            if result.change_info:
                console.print("\n[cyan]Change Info:[/cyan]")
                change_table = Table(show_header=False, box=None)
                change_table.add_column("Key", style="cyan")
                change_table.add_column("Value", style="white")
                for key, value in result.change_info.items():
                    change_table.add_row(key, str(value))
                console.print(change_table)

    except AuthenticationError as e:
        err_console.print(
            f"[red]Authentication failed:[/red] {e}\n"
            "[yellow]Hint:[/yellow] Set JSCOM_API_TOKEN env var or use --token option"
        )
        raise typer.Exit(code=2) from None
    except ValidationError as e:
        err_console.print(f"[red]Validation error:[/red] {e}")
        raise typer.Exit(code=1) from None
    except NetworkError as e:
        err_console.print(f"[red]Network error:[/red] {e}")
        raise typer.Exit(code=1) from None
    except ServerError as e:
        err_console.print(f"[red]Server error:[/red] {e}")
        raise typer.Exit(code=1) from None
    except JscomApiError as e:
        err_console.print(f"[red]API error:[/red] {e}")
        raise typer.Exit(code=1) from None
    except Exception as e:
        err_console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(code=1) from None


if __name__ == "__main__":
    app()
