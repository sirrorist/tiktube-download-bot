"""Middleware for the bot."""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from datetime import datetime
from sqlalchemy import select, update

from database import get_db, User
from config import settings


class UserMiddleware(BaseMiddleware):
    """Middleware to track and update user information."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process user data."""
        tg_user: TgUser = data.get("event_from_user")
        if not tg_user:
            return await handler(event, data)
        
        async for session in get_db():
            # Get or create user
            result = await session.execute(
                select(User).where(User.id == tg_user.id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(
                    id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                    last_name=tg_user.last_name,
                    is_premium=tg_user.is_premium or False,
                )
                session.add(user)
                await session.commit()
            else:
                # Update user info
                user.username = tg_user.username
                user.first_name = tg_user.first_name
                user.last_name = tg_user.last_name
                user.is_premium = tg_user.is_premium or user.is_premium
                user.last_activity = datetime.utcnow()
                await session.commit()
            
            data["user"] = user
            break
        
        return await handler(event, data)


class RateLimitMiddleware(BaseMiddleware):
    """Middleware to enforce rate limiting."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Check rate limits."""
        user: User = data.get("user")
        if not user:
            return await handler(event, data)
        
        # Reset daily counter if needed
        if user.last_activity and user.last_activity.date() < datetime.utcnow().date():
            async for session in get_db():
                await session.execute(
                    update(User)
                    .where(User.id == user.id)
                    .values(downloads_today=0)
                )
                await session.commit()
                user.downloads_today = 0
                break
        
        # Check limit
        limit = settings.premium_user_limit if user.is_premium else settings.free_user_limit
        
        if user.downloads_today >= limit:
            # This will be handled in handlers
            data["rate_limited"] = True
        else:
            data["rate_limited"] = False
        
        return await handler(event, data)
