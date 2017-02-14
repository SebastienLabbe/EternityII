import argparse
import os

import time

import datetime

import timed_loop
import dill as dill

import ind
from puzzle import Puzzle

# WINDOWS TROUBLE ><
os.environ['TCL_LIBRARY'] = "C:\\Python27\\tcl\\tcl8.5"
os.environ['TK_LIBRARY'] = "C:\\Python27\\tcl\\tk8.5"

import config

def _load_file(s):
  try:
    with open(s, "r") as e:
      return dill.load(e)
  except Exception as e:
    print e
    return None

def load_population(old_pop):
  if old_pop:
    f = _load_file(config.population_file_saved)
    if f != None: # Todo Save a basic population and reload it in the Puzzle
      print "Old Population Loaded"
      return f

  # Loading a basic Population with a runner
  inds = ind.get_population()
  corner = [i for i in inds if i[1].count(0) == 2]
  border = [i for i in inds if i[1].count(0) == 1]
  inside = [i for i in inds if i[1].count(0) == 0]
  return Puzzle((corner, border, inside))


def save_population(puzzle):
  with open(config.population_file_saved, "w") as f:
    dill.dump(puzzle, f)
  print "Saved @%s" % config.population_file_saved

def one_turn(puzzle, generation, write_stats):
  # Example of call
  removed_tils = puzzle.select(generation)
  # Example of call
  puzzle.crossover(removed_tils)
  # Example of call
  n_mutated = puzzle.mutate()
  # Evaluate the entire population
  puzzle.evaluate()
  if write_stats:
    # If you want log the different data
    puzzle.log_stats(generation, n_mutated)
  if puzzle.population[0].fitness_group.values[0] == config.score_group_max:
    return True
  return False


def loop(puzzle, write_stats, nloop=None, timer=None):
  """

  :param puzzle:
  :param write_stats:
  :param nloop: argparse set nloop to config.ngen if not set.
  :param time:
  :return:
  """
  end_time = None
  iteration = 0
  if timer:
    end_time = time.time() + datetime.timedelta(minutes=timer).total_seconds()

  while (nloop == -1 or iteration < nloop) and (end_time is None or time.time() < end_time):

    if one_turn(puzzle, iteration, write_stats):
      print "Solution Found !"
      if write_stats:
        # Saving logbook
        puzzle.write_stats()
      return True
    if iteration % 500 == 0 and iteration != 0:
      # Write the populations to a file to free some memory
      puzzle.stats.free_memory()
    iteration += 1

  print "No Solution Look at the logbook."
  if write_stats:
    # Saving logbook
    puzzle.write_stats()
    save_population(puzzle)

def main(write_stats, old_pop=False, timer=None, nloop=None, timed=False):
  try:
    os.mkdir("./gen/")
  except Exception as e:
    pass

  puzzle = load_population(old_pop)
  if timed:
    timed_loop.timed_loop(puzzle, write_stats, (one_turn, save_population), timer=timer, nloop=nloop)
  else:
    loop(puzzle, write_stats, timer=timer, nloop=nloop)

def get_args():
  help="""Run a population with arguments and config file.
  """
  parser = argparse.ArgumentParser(description=help)
  parser.add_argument('--loop', '-l', action='store', default=config.NGEN,
                      help='Number of loop maximum to do. if set to -1 infinite loop (use time to stop) (default: config.NGEN %s)' % config.NGEN)
  parser.add_argument('--time', '-t', action='store', default=None,
                      help='Maximum time to execute the loop in min')
  parser.add_argument('--timed', action='store_true', default=False,
                      help='iteration and loop would be timed. benchmark.')
  parser.add_argument('--old-pop', '-o', action='store_true', default=False,
                      help='Load an old population. path is set in config file current is @%s.' % config.population_file_saved)
  args = parser.parse_args()
  return args

if __name__ == '__main__':
  kwargs = get_args()
  main(True, old_pop=kwargs.old_pop, timed=kwargs.timed,
       timer=None if kwargs.time is None else float(kwargs.time),
       nloop=int(kwargs.loop))
