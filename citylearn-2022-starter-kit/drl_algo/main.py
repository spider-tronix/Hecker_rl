import argparse
import datetime
import gym
import numpy as np
import itertools
import torch
from sac import SAC
# from torch.utils.tensorboard import SummaryWriter
from citylearn.citylearn import CityLearnEnv
from replay_memory import ReplayMemory
import wandb

parser = argparse.ArgumentParser(description='PyTorch Soft Actor-Critic Args')
parser.add_argument('--env-name', default="Citylearn",
                    help='Mujoco Gym environment (default: HalfCheetah-v2)')
parser.add_argument('--policy', default="Gaussian",
                    help='Policy Type: Gaussian | Deterministic (default: Gaussian)')
parser.add_argument('--eval', type=bool, default=True,
                    help='Evaluates a policy a policy every 10 episode (default: True)')
parser.add_argument('--gamma', type=float, default=0.99, metavar='G',
                    help='discount factor for reward (default: 0.99)')
parser.add_argument('--tau', type=float, default=0.005, metavar='G',
                    help='target smoothing coefficient(τ) (default: 0.005)')
parser.add_argument('--lr', type=float, default=0.0003, metavar='G',
                    help='learning rate (default: 0.0003)')
parser.add_argument('--alpha', type=float, default=0.2, metavar='G',
                    help='Temperature parameter α determines the relative importance of the entropy\
                            term against the reward (default: 0.2)')
parser.add_argument('--automatic_entropy_tuning', type=bool, default=False, metavar='G',
                    help='Automaically adjust α (default: False)')
parser.add_argument('--seed', type=int, default=123456, metavar='N',
                    help='random seed (default: 123456)')
parser.add_argument('--batch_size', type=int, default=256, metavar='N',
                    help='batch size (default: 256)')
parser.add_argument('--num_steps', type=int, default=1000001, metavar='N',
                    help='maximum number of steps (default: 1000000)')
parser.add_argument('--hidden_size', type=int, default=256, metavar='N',
                    help='hidden size (default: 256)')
parser.add_argument('--updates_per_step', type=int, default=1, metavar='N',
                    help='model updates per simulator step (default: 1)')
parser.add_argument('--start_steps', type=int, default=10000, metavar='N',
                    help='Steps sampling random actions (default: 10000)')
parser.add_argument('--target_update_interval', type=int, default=1, metavar='N',
                    help='Value target update per no. of updates per step (default: 1)')
parser.add_argument('--replay_size', type=int, default=1000000, metavar='N',
                    help='size of replay buffer (default: 10000000)')
parser.add_argument('--cuda', action="store_true",
                    help='run on CUDA (default: False)')
parser.add_argument('--reward_key', type=int)

args = parser.parse_args()

# Environment
# env = NormalizedActions(gym.make(args.env_name))

class Constants:
    episodes = 3
    schema_path = 'citylearn-2022-starter-kit/data/citylearn_challenge_2022_phase_1/schema.json'

import os
os.mkdir("KEY"+str(args.reward_key))
env = CityLearnEnv(schema=Constants.schema_path)
os.rmdir("KEY"+str(args.reward_key))

env.seed(123456)

torch.manual_seed(args.seed)
np.random.seed(args.seed)

# Agent
agent = SAC(env.observation_space[0].shape[0], env.action_space, args)

#Tesnorboard
# writer = SummaryWriter('runs/{}_SAC_{}_{}_{}'.format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), args.env_name,
#                                                              args.policy, "autotune" if args.automatic_entropy_tuning else ""))

wandb.init(project="REWARD_SWEEP",name="reward_{}_sac-{}-lr:{}_gamma:{}_tau:{}_alpha:{}".format(args.reward_key,args.policy,args.lr,args.gamma,args.tau,args.alpha),entity="cleancity_challenge_rl")
# Memory
memory = ReplayMemory(args.replay_size, args.seed)

# Training Loop
total_numsteps = 0
updates = 0

for i_episode in itertools.count(1):
    episode_reward = 0
    episode_steps = 0
    done = False
    state = env.reset()

    for x_ in range(1000):
        # print(f"EPISODE STEPS: {episode_steps}", end="\r")
        if args.start_steps > total_numsteps:
            action = [i.sample() for i in env.action_space]  # Sample random action

        else:
            action = agent.select_action(state)
            action = [np.asarray([i]) for i in action]

        if len(memory) > args.batch_size:
            # Number of updates per step in environment
            # for i in range(args.updates_per_step):
            #     # Update parameters of all the networks
                critic_1_loss, critic_2_loss, policy_loss, ent_loss, alpha = agent.update_parameters(memory, args.batch_size, updates)
                wandb.log({'loss/critic_1': critic_1_loss,'loss/critic_2': critic_2_loss, 'loss/policy': policy_loss, 'loss/entropy_loss': ent_loss, 'entropy_temprature/alpha':alpha})

                updates += 1
        
        next_state, reward, done, _ = env.step(action) # Step
        episode_steps += 1
        total_numsteps += 1
        episode_reward += reward

        # Ignore the "done" signal if it comes from hitting the time horizon.
        # (https://github.com/openai/spinningup/blob/master/spinup/algos/sac/sac.py)
        mask = float(not done)

        memory.push(state, action, reward, next_state, mask) # Append transition to memory

        state = next_state

    if total_numsteps > args.num_steps:
        break

    # for k_, k in enumerate(episode_reward):
    #     writer.add_scalar(f'reward/Building {k_}', k, i_episode)

    print("Episode: {}, total numsteps: {}, episode steps: {}, reward: {}".format(i_episode, total_numsteps, episode_steps, episode_reward))
    wandb.log({"score":sum(episode_reward),"Building_Score_1":episode_reward[0],"Building_Score_2":episode_reward[1],"Building_Score_3":episode_reward[2],"Building_Score_4":episode_reward[3],"Building_Score_5":episode_reward[4]})

env.close()
