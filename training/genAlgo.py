from game.agent import STRATEGIES, Agent
from game.game import Game
from training.allActions import AllActionsModel
from datetime import datetime
import time
import numpy as np
import tensorflow as tf
import os

class GeneticAlgorithm():

  def __init__(self, pop_size=54, agents_per_game=3):
    self.agents_per_game = agents_per_game
    self.pop_size = pop_size
    self.population = []
    self.generations = 0
    self.current_time = datetime.now().strftime("%Y-%m-%d_%H:%M")
    log_dir = 'logs/genetic/' + self.current_time
    self.summary_writer = tf.summary.create_file_writer(log_dir)

    self.init_population()
  
  def init_population(self):
    available_strategies = [strategy for strategy in STRATEGIES if strategy is not STRATEGIES.RANDOM]

    for _ in range(self.pop_size):
      strategy = np.random.choice(available_strategies)
      self.population.append(Agent(strategy))

  def run_game(self, game_index):
    agents = self.population[game_index*self.agents_per_game:self.agents_per_game+self.agents_per_game*game_index]
    game = Game(agents)
    game.run_game()
    return game.time, game.num_turns, agents[agents.index(game.winner)]

  def run_generations(self, n):
    for _ in range(n):
      start_time = time.time()
      self.generations += 1
      np.random.shuffle(self.population)
      game_times = []
      game_turns = []
      winners = []
      for game_index in range(int(round(self.pop_size / self.agents_per_game))):
        game_time, turns, winner = self.run_game(game_index)
        game_times.append(game_time)
        game_turns.append(turns)
        winners.append(winner)
      
      # Recreate population
      self.population = winners

      while len(self.population) < self.pop_size:
        for w1 in winners:
          for w2 in winners:
            if len(self.population) < self.pop_size and not w1 == w2:
              new_agent = w1.mix_weights(w2)
              self.population.append(new_agent)

      # Saving models
      if self.generations % 2 == 0:
        to_save = winners[:3]
        save_path = 'models/genetic/' + str(self.generations) + '/' + self.current_time
        os.makedirs(save_path)
        for idx, agent in enumerate(to_save):
          agent.model.save(save_path + '/model' + str(idx))

      # Logging 
      average_game_time = np.sum(game_times) / len(game_times)
      average_game_turns = np.sum(game_turns) / len(game_turns)
      print('------ Generation', self.generations, '------ time: %s' % (time.time() - start_time))
      print('Average time', average_game_time)
      print('Average turns', average_game_turns)
      with self.summary_writer.as_default():
        tf.summary.scalar('Average game time', average_game_time, step=self.generations)
        tf.summary.scalar('Average game turns', average_game_turns, step=self.generations)
