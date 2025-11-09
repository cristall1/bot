"""
Tests for alert service
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from services.alert_service import AlertService
from services.user_service import UserService
from models import AlertType, Alert, UserAlertPreference, User


@pytest.mark.asyncio
async def test_create_alert(db_session: AsyncSession, admin_user: User):
    """Test creating an alert"""
    alert = await AlertService.create_alert(
        db_session,
        alert_type=AlertType.MISSING_PERSON,
        creator_id=admin_user.id,
        title="Пропал Иван Иванов",
        description="Пропал человек 30 лет, рост 180см",
        phone="+998901234567",
        address_text="Ташкент, район Юнусабад",
        expires_hours=48
    )
    
    assert alert is not None
    assert alert.id is not None
    assert alert.alert_type == AlertType.MISSING_PERSON
    assert alert.creator_id == admin_user.id
    assert alert.title == "Пропал Иван Иванов"
    assert alert.is_approved == False
    assert alert.is_moderated == False
    assert alert.expires_at is not None


@pytest.mark.asyncio
async def test_get_alert(db_session: AsyncSession, admin_user: User):
    """Test getting alert by ID"""
    # Create alert
    alert = await AlertService.create_alert(
        db_session,
        alert_type=AlertType.SHURTA,
        creator_id=admin_user.id,
        description="Драка на улице",
        address_text="Ташкент, ул. Навои"
    )
    
    # Get alert
    fetched = await AlertService.get_alert(db_session, alert.id)
    
    assert fetched is not None
    assert fetched.id == alert.id
    assert fetched.alert_type == AlertType.SHURTA
    assert fetched.creator is not None
    assert fetched.creator.id == admin_user.id


@pytest.mark.asyncio
async def test_get_pending_alerts(db_session: AsyncSession, admin_user: User):
    """Test getting pending alerts"""
    # Create multiple alerts
    await AlertService.create_alert(
        db_session,
        alert_type=AlertType.MISSING_PERSON,
        creator_id=admin_user.id,
        description="Alert 1"
    )
    await AlertService.create_alert(
        db_session,
        alert_type=AlertType.LOST_ITEM,
        creator_id=admin_user.id,
        description="Alert 2"
    )
    
    # Get all pending
    pending = await AlertService.get_pending_alerts(db_session)
    assert len(pending) >= 2
    
    # Get filtered by type
    filtered = await AlertService.get_pending_alerts(
        db_session,
        alert_type=AlertType.MISSING_PERSON
    )
    assert len(filtered) >= 1
    assert all(a.alert_type == AlertType.MISSING_PERSON for a in filtered)


@pytest.mark.asyncio
async def test_pending_count_by_type(db_session: AsyncSession, admin_user: User):
    """Test counting pending alerts by type"""
    # Create alerts of different types
    await AlertService.create_alert(
        db_session,
        alert_type=AlertType.MISSING_PERSON,
        creator_id=admin_user.id,
        description="Person 1"
    )
    await AlertService.create_alert(
        db_session,
        alert_type=AlertType.MISSING_PERSON,
        creator_id=admin_user.id,
        description="Person 2"
    )
    await AlertService.create_alert(
        db_session,
        alert_type=AlertType.SHURTA,
        creator_id=admin_user.id,
        description="Police alert"
    )
    
    # Get counts
    counts = await AlertService.get_pending_count_by_type(db_session)
    
    assert AlertType.MISSING_PERSON.value in counts
    assert counts[AlertType.MISSING_PERSON.value] >= 2
    assert counts[AlertType.SHURTA.value] >= 1


@pytest.mark.asyncio
async def test_approve_alert(db_session: AsyncSession, admin_user: User):
    """Test approving an alert"""
    # Create alert
    alert = await AlertService.create_alert(
        db_session,
        alert_type=AlertType.COURIER_NEEDED,
        creator_id=admin_user.id,
        description="Доставка посылки"
    )
    
    # Approve
    approved = await AlertService.approve_alert(
        db_session,
        alert_id=alert.id,
        moderator_id=admin_user.id
    )
    
    assert approved is not None
    assert approved.is_approved == True
    assert approved.is_moderated == True
    assert approved.moderator_id == admin_user.id
    assert approved.moderated_at is not None


@pytest.mark.asyncio
async def test_reject_alert(db_session: AsyncSession, admin_user: User):
    """Test rejecting an alert"""
    # Create alert
    alert = await AlertService.create_alert(
        db_session,
        alert_type=AlertType.JOB_POSTING,
        creator_id=admin_user.id,
        description="Вакансия программиста"
    )
    
    # Reject
    rejected = await AlertService.reject_alert(
        db_session,
        alert_id=alert.id,
        moderator_id=admin_user.id,
        reason="Недостаточно информации"
    )
    
    assert rejected is not None
    assert rejected.is_approved == False
    assert rejected.is_moderated == True
    assert rejected.is_active == False
    assert rejected.rejection_reason == "Недостаточно информации"
    assert rejected.moderator_id == admin_user.id


@pytest.mark.asyncio
async def test_get_broadcast_targets(db_session: AsyncSession, admin_user: User, regular_user: User):
    """Test getting broadcast target users"""
    # Create alert with language filter
    alert = await AlertService.create_alert(
        db_session,
        alert_type=AlertType.EVENT_ANNOUNCEMENT,
        creator_id=admin_user.id,
        description="Мероприятие",
        target_languages=["RU"]
    )
    
    # Approve alert
    await AlertService.approve_alert(db_session, alert.id, admin_user.id)
    
    # Get targets
    targets = await AlertService.get_broadcast_targets(db_session, alert)
    
    assert isinstance(targets, list)
    # Should include users with RU language
    target_ids = [u.id for u in targets]
    if regular_user.language == "RU" and not regular_user.is_banned:
        assert regular_user.id in target_ids


@pytest.mark.asyncio
async def test_mark_broadcast_sent(db_session: AsyncSession, admin_user: User):
    """Test marking alert as broadcast"""
    # Create and approve alert
    alert = await AlertService.create_alert(
        db_session,
        alert_type=AlertType.EVENT_ANNOUNCEMENT,
        creator_id=admin_user.id,
        description="Объявление"
    )
    await AlertService.approve_alert(db_session, alert.id, admin_user.id)
    
    # Mark as broadcast
    updated = await AlertService.mark_broadcast_sent(
        db_session,
        alert_id=alert.id,
        recipient_count=150
    )
    
    assert updated is not None
    assert updated.broadcast_sent == True
    assert updated.broadcast_count == 150
    assert updated.broadcast_at is not None


@pytest.mark.asyncio
async def test_user_preferences(db_session: AsyncSession, regular_user: User):
    """Test user alert preferences"""
    # Get default preferences (all should be enabled)
    prefs = await AlertService.get_user_preferences(db_session, regular_user.id)
    
    assert AlertType.MISSING_PERSON in prefs
    assert prefs[AlertType.MISSING_PERSON] == True  # Default enabled
    
    # Disable one type
    await AlertService.update_user_preference(
        db_session,
        user_id=regular_user.id,
        alert_type=AlertType.MISSING_PERSON,
        is_enabled=False
    )
    
    # Check updated preference
    prefs = await AlertService.get_user_preferences(db_session, regular_user.id)
    assert prefs[AlertType.MISSING_PERSON] == False
    
    # Enable it back
    await AlertService.update_user_preference(
        db_session,
        user_id=regular_user.id,
        alert_type=AlertType.MISSING_PERSON,
        is_enabled=True
    )
    
    prefs = await AlertService.get_user_preferences(db_session, regular_user.id)
    assert prefs[AlertType.MISSING_PERSON] == True


@pytest.mark.asyncio
async def test_alert_statistics(db_session: AsyncSession, admin_user: User):
    """Test getting alert statistics"""
    # Create various alerts
    alert1 = await AlertService.create_alert(
        db_session,
        alert_type=AlertType.LOST_ITEM,
        creator_id=admin_user.id,
        description="Продажа авто"
    )
    alert2 = await AlertService.create_alert(
        db_session,
        alert_type=AlertType.JOB_POSTING,
        creator_id=admin_user.id,
        description="Услуга репетитора"
    )
    
    # Approve one
    await AlertService.approve_alert(db_session, alert1.id, admin_user.id)
    
    # Get statistics
    stats = await AlertService.get_alert_statistics(db_session)
    
    assert "total_pending" in stats
    assert "total_approved" in stats
    assert "pending_by_type" in stats
    assert stats["total_approved"] >= 1
    assert stats["total_pending"] >= 1


@pytest.mark.asyncio
async def test_get_approved_alerts(db_session: AsyncSession, admin_user: User):
    """Test getting approved alerts"""
    # Create and approve alert
    alert = await AlertService.create_alert(
        db_session,
        alert_type=AlertType.ACCOMMODATION_NEEDED,
        creator_id=admin_user.id,
        description="Сдается квартира"
    )
    await AlertService.approve_alert(db_session, alert.id, admin_user.id)
    
    # Get approved alerts
    approved = await AlertService.get_approved_alerts(db_session)
    
    assert len(approved) >= 1
    assert all(a.is_approved for a in approved)
    assert alert.id in [a.id for a in approved]


@pytest.mark.asyncio
async def test_alert_with_location(db_session: AsyncSession, admin_user: User):
    """Test creating alert with location"""
    alert = await AlertService.create_alert(
        db_session,
        alert_type=AlertType.MEDICAL_EMERGENCY,
        creator_id=admin_user.id,
        description="ДТП на перекрестке",
        location_type="GEO",
        latitude=41.2995,
        longitude=69.2401,
        geo_name="Ташкент, проспект Амира Темура"
    )
    
    assert alert.location_type == "GEO"
    assert alert.latitude == 41.2995
    assert alert.longitude == 69.2401
    assert alert.geo_name == "Ташкент, проспект Амира Темура"


@pytest.mark.asyncio
async def test_alert_with_filters(db_session: AsyncSession, admin_user: User):
    """Test creating alert with target filters"""
    alert = await AlertService.create_alert(
        db_session,
        alert_type=AlertType.EVENT_ANNOUNCEMENT,
        creator_id=admin_user.id,
        description="Мероприятие только для граждан УЗ",
        target_languages=["UZ"],
        target_citizenships=["UZ"],
        target_couriers_only=False
    )
    
    assert alert.target_languages == ["UZ"]
    assert alert.target_citizenships == ["UZ"]
    assert alert.target_couriers_only == False
