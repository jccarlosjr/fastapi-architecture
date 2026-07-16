import asyncio
import re
from typing import Any
import typer
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.modules.accounts.models import User
from app.modules.permissions.models import Permission
from app.modules.groups.models import Group
from app.core.security import hash_password

app = typer.Typer(help="FastAPI Minimal CLI Management Tool")


def validate_email(email: str) -> bool:
    regex = r"^\S+@\S+\.\S+$"
    return bool(re.match(regex, email))


async def create_superuser_async(email: str, full_name: str, password: str) -> None:
    async with AsyncSessionLocal() as session:
        # Check if email is already taken
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            typer.echo(f"Error: User with email '{email}' already exists.", err=True)
            raise typer.Exit(code=1)

        # Create user object
        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role="admin",
            is_active=True,
            is_verified=True,
            is_superuser=True,
            is_staff=True,
        )
        session.add(user)
        await session.commit()
        typer.echo(f"Superuser '{email}' created successfully.")


async def seed_permissions_async() -> None:
    # Standard models and their CRUD actions
    models = ["user", "group", "permission"]
    actions = ["view", "add", "change", "delete"]

    async with AsyncSessionLocal() as session:
        created_count = 0
        skipped_count = 0

        for model in models:
            for action in actions:
                codename = f"{action}_{model}"
                name = f"Can {action} {model}"

                # Check if permission exists
                stmt = select(Permission).where(Permission.codename == codename)
                result = await session.execute(stmt)
                existing_permission = result.scalar_one_or_none()

                if not existing_permission:
                    perm = Permission(
                        name=name,
                        codename=codename
                    )
                    session.add(perm)
                    created_count += 1
                else:
                    skipped_count += 1

        await session.commit()
        typer.echo(f"Permissions seeded: {created_count} created, {skipped_count} already existed.")


@app.command(name="createsuperuser")
def create_superuser() -> None:
    """Create a new superuser with administrative privileges."""
    typer.echo("--- Create Superuser ---")
    
    # 1. Prompt and validate Email
    while True:
        email = typer.prompt("Email Address").strip().lower()
        if not validate_email(email):
            typer.echo("Error: Invalid email format. Try again.", err=True)
            continue
        break

    # 2. Prompt Full Name
    while True:
        full_name = typer.prompt("Full Name").strip()
        if not full_name:
            typer.echo("Error: Full name is required. Try again.", err=True)
            continue
        break

    # 3. Prompt and confirm Password
    while True:
        password = typer.prompt("Password", hide_input=True)
        if len(password) < 8:
            typer.echo("Error: Password must be at least 8 characters long. Try again.", err=True)
            continue
        
        password_confirm = typer.prompt("Confirm Password", hide_input=True)
        if password != password_confirm:
            typer.echo("Error: Passwords do not match. Try again.", err=True)
            continue
        break

    asyncio.run(create_superuser_async(email, full_name, password))


@app.command(name="seed-permissions")
def seed_permissions() -> None:
    """Seed default CRUD permissions for User, Group, and Permission models."""
    typer.echo("--- Seeding Permissions ---")
    asyncio.run(seed_permissions_async())


if __name__ == "__main__":
    app()
