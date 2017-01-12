import pytest
from brownie import Wei, ZERO_ADDRESS


@pytest.fixture(scope="function", autouse=True)
def shared_setup(fn_isolation):
    pass


@pytest.fixture(scope='module')
def ape(accounts):
    return accounts[0]


@pytest.fixture()
def steth_whale(accounts, steth_token, lido, lp_token):
    acct = accounts[1]
    lido.submit(ZERO_ADDRESS, {"from": acct, "value": "10 ether"})
    assert steth_token.balanceOf(acct) > 0
    assert lp_token.balanceOf(acct) == 0
    return acct


@pytest.fixture(scope='module')
def stranger(accounts):
    return accounts[9]


@pytest.fixture(scope='module')
def curve_farmer(accounts, gauge):
    # already deposited to the steth gauge
    acct = accounts.at("0x32199f1fFD5C9a5745A98FE492570a8D1601Dc4C", force=True)
    assert gauge.balanceOf(acct) > 0
    return acct


# Lido DAO Voting app
@pytest.fixture(scope='module')
def dao_voting(accounts):
    return accounts.at("0x2e59A20f205bB85a89C53f1936454680651E618e", force=True)


@pytest.fixture(scope='module')
def lido(interface):
    return interface.Lido("0xae7ab96520de3a18e5e111b5eaab095312d7fe84")


@pytest.fixture(scope='module')
def steth_token(interface, lido):
    return interface.ERC20(lido.address)


# Lido DAO Agent app
@pytest.fixture(scope='module')
def dao_agent(interface):
    return interface.Agent("0x3e40D73EB977Dc6a537aF587D48316feE66E9C8c")


@pytest.fixture(scope='module')
def steth_pool(interface):
    return interface.StableSwapSTETH("0xDC24316b9AE028F1497c275EB9192a3Ea0f67022")


@pytest.fixture(scope='module')
def lp_token(steth_pool, interface):
    token_address = steth_pool.lp_token()
    return interface.ERC20(token_address)


@pytest.fixture(scope='module')
def ldo_token(interface):
    return interface.ERC20("0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32")


@pytest.fixture(scope='module')
def gauge(interface):
    return interface.LiquidityGaugeV2("0x182B723a58739a9c974cFDB385ceaDb237453c28")


@pytest.fixture(scope='module')
def gauge_admin(gauge, accounts):
    return accounts.at(gauge.admin(), force=True)


class RewardsHelpers:
    StakingRewards = None
    RewardsManager = None

    @staticmethod
    def deploy_rewards(rewards_period, reward_amount, dao_agent, lp_token, rewards_token, deployer):
        manager = RewardsHelpers.RewardsManager.deploy({"from": deployer})

        rewards = RewardsHelpers.StakingRewards.deploy(
            dao_agent, # _owner
            manager, # _rewardsDistribution
            rewards_token, # _rewardsToken
            lp_token, # _stakingToken
            rewards_period, # _rewardsDuration
            {"from": deployer}
        )

        manager.set_rewards_contract(rewards, {"from": deployer})
        manager.set_reward_amount(reward_amount, {"from": deployer})

        assert manager.rewards_contract() == rewards
        assert manager.reward_amount() == reward_amount

        manager.transfer_ownership(dao_agent, {"from": deployer})

        return {"manager": manager, "rewards": rewards}

    @staticmethod
    def install_rewards(gauge, gauge_admin, rewards_token, rewards):
        sigs = [
            rewards.stake.signature[2:],
            rewards.withdraw.signature[2:],
            rewards.getReward.signature[2:]
        ]
        gauge.set_rewards(
            rewards, # _reward_contract
            f"0x{sigs[0]}{sigs[1]}{sigs[2]}{'00' * 20}", # _sigs
            [rewards_token] + [ZERO_ADDRESS] * 7, # _reward_tokens
            {"from": gauge_admin}
        )
        assert gauge.reward_contract() == rewards
        assert gauge.reward_tokens(0) == rewards_token
        assert gauge.reward_tokens(1) == ZERO_ADDRESS


@pytest.fixture(scope='module')
def rewards_helpers(StakingRewards, RewardsManager):
    RewardsHelpers.StakingRewards = StakingRewards
    RewardsHelpers.RewardsManager = RewardsManager
    return RewardsHelpers


class Helpers:
    @staticmethod
    def filter_events_from(addr, events):
      return list(filter(lambda evt: evt.address == addr, events))

    @staticmethod
    def assert_single_event_named(evt_name, tx, evt_keys_dict):
      receiver_events = Helpers.filter_events_from(tx.receiver, tx.events[evt_name])
      assert len(receiver_events) == 1
      assert dict(receiver_events[0]) == evt_keys_dict


@pytest.fixture(scope='module')
def helpers():
    return Helpers
