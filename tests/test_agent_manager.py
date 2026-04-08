"""Tests for agent management."""

import pytest
from src.models.schemas import AgentUser, IncomingMessage, MessageSource
from src.agents.agent_manager import register_user, get_user, find_user_by_name, get_all_users
from src.agents.router import detect_target_agent, route_message


@pytest.fixture(autouse=True)
def setup_users():
    """Register test users before each test."""
    from src.agents.agent_manager import _user_registry
    _user_registry.clear()

    register_user(AgentUser(
        user_id="user_1",
        display_name="Sarah Johnson",
        email="sarah@rentor.ca",
        role="Property Manager",
        department="Operations",
    ))
    register_user(AgentUser(
        user_id="user_2",
        display_name="Mike Chen",
        email="mike@rentor.ca",
        role="Maintenance Lead",
        department="Maintenance",
    ))


def test_register_and_get_user():
    user = get_user("user_1")
    assert user is not None
    assert user.display_name == "Sarah Johnson"


def test_get_all_users():
    users = get_all_users()
    assert len(users) == 2


def test_find_user_by_name():
    user = find_user_by_name("Sarah")
    assert user is not None
    assert user.user_id == "user_1"


def test_find_user_by_name_case_insensitive():
    user = find_user_by_name("mike")
    assert user is not None
    assert user.user_id == "user_2"


def test_find_user_by_name_not_found():
    user = find_user_by_name("Nobody")
    assert user is None


def test_detect_target_agent():
    target = detect_target_agent("ask Sarah's agent about the lease policy")
    assert target == "user_1"


def test_detect_target_agent_no_match():
    target = detect_target_agent("what is the pet policy?")
    assert target is None


def test_route_message_cross_agent():
    msg = IncomingMessage(
        source=MessageSource.API,
        sender_id="user_2",
        sender_name="Mike Chen",
        text="ask Sarah's agent about the lease terms",
    )
    routed = route_message(msg)
    assert routed.target_agent_user_id == "user_1"


def test_route_message_direct():
    msg = IncomingMessage(
        source=MessageSource.API,
        sender_id="user_1",
        sender_name="Sarah Johnson",
        text="what is the pet deposit policy?",
    )
    routed = route_message(msg)
    assert routed.target_agent_user_id is None
