import pytest

from app.models import Account, User  # Assuming this is your User model

from flask.testing import FlaskClient
from app import create_app  # Assuming your app is created like this

@pytest.fixture
def client() -> FlaskClient:
    app = create_app()
    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client

async def user_factory(session, name, email, password):
    """
    Helper function to create account
    """
    user = User(name=name, email=email, password=password)
    session.add(user)
    await session.commit()
    return user

def delete_user(session, user):
    session.delete(user)
    session.commit()

def account_factory(session, user_id, name, password, account_number):
    """
    Helper function to create account
    """
    account = Account(user_id=user_id, name=name, password=password, account_number=account_number)
    session.add(account)
    session.commit()
    return account

@pytest.mark.asyncio
async def test_create_user_account(client, session):
    """
    Test Account Creating Logic
    """
    # GIVEN
    name = "test_user_1"
    email = "test_27@kakao.com"
    password = "password"

    # WHEN
    with client.application.app_context():  # Enter the application context
        user = await user_factory(session, name, email, password)
        
        # Login the user
        login_data = {
            'username': name,
            'password': password
        }
        client.post('/auth/login', data=login_data)


        # THEN
        print(user.name)
        print(user.email)
        print(user.password_hash)
        print(user.id)

        assert user.name == name
        assert user.email == email

        # Mock the Flask `g` object with a user
        # with client.application.app_context():
            

        # Call the AccountListView's POST method
    # with client.application.app_context():
        response = client.post("/accounts/", json={"name": name, "password": password, "user_id":user.id, "account_number": "5555111234567"})

    # Validate the response
    assert response.status_code == 201
    assert response.json == {
        "message": "Account created successfully",
        "account": {},
    }

    # with client.application.app_context():  # Enter the application context
    #     delete_user(session, user)

    # await session.rollback()


# def card_factory(account_id):
#     """
#     Helper function to register card to a user
#     """
#     card = Mock()
#     card.id = 1
#     card.account_id = account_id
#     card.is_enabled = True
#     card.balance = 0

#     return card


# @pytest.mark.asyncio
# async def test_register_cards():

#     #GIVEN
#     _account = account_factory()

#     #WHEN
#         # Card Registration Logic
#     #THEN
#         # Assertion


# @pytest.mark.asyncio
# async def test_disable_card():
#     #GIVEN
#     _account = account_factory()
#     _card = card_factory(account_id=...)

#     #WHEN
#         # Card Disabling Logic
#     #THEN
#         #Assertion

# @pytest.mark.asyncio
# async def test_enable_card():
#     #GIVEN
#     _account = account_factory()
#     _card = card_factory(account_id=...)

#     #WHEN
#         # Card Enabling Logic
            
#     #THEN
#         #Assertion
            


# @pytest.mark.asyncio
# async def test_deposit_cash():
#     #GIVEN
#     _account = account_factory()
#     _card = card_factory(account_id=...)

#     #WHEN
#         # Money Saving Logic

#     #THEN

# @pytest.mark.asyncio
# async def test_withdraw_cash():
#     #GIVEN
#     _account = account_factory()
#     _card = card_factory(account_id=...)

#     #WHEN
#         # Money Withdrawing Logic

#     #THEN



# @pytest.mark.asyncio
# async def test_check_account_balance():
#     ...
#     #GIVEN
#     _account = account_factory()
#     _card = card_factory(account_id=...)

#     #WHEN
#         # Balace checking Logic
            
#     #THEN
#         #Assertion