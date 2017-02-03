import getpass
import random
import copy
import string

import matplotlib.pyplot as plt
import numpy
import os
import statistics
from deap import base
from deap import creator
from deap import tools
import config
import ind
import eternity
# Not use for now but for easier read i guess all eval code should go there.
import eval

# Coins Hautgauche, Hautdroit, basGauche, basDroit
CORNER_POS = [0, 15, 240, 255]
# Mask des coins Hautgauche, Hautdroit, basGauche, basDroit
MASK_CORNERS = [[0, None, None, 0], [0, 0, None, None], [None, None, 0, 0], [None, 0, 0, None]]
BORDER_TOP = range(1, 15)
BORDER_BOT = range(241, 255)
BODER_LEFT = [31, 47, 63, 79, 95, 111, 127, 143, 159, 175, 191, 207, 223, 239]
BORDER_RIGHT = [16, 32, 48, 64, 80, 96, 112, 128, 144, 160, 176, 192, 208, 224]
# Tout les position de X pour les Bords
BORDER_POS = BORDER_TOP + BORDER_BOT + BODER_LEFT + BORDER_RIGHT
# Represent les mask des Bordures
MASK_TOP = [0, None, None, None]
MASK_BOT = [None, None, 0, None]
MASK_LEFT = [None, 0, None, None]
MASK_RIGHT = [None, None, None, 0]
# Toutes les positions de X en dehors des coins et des bords
INSIDE_POS = [x for x in range(0, 255) if x not in CORNER_POS and x not in BORDER_POS]

class Puzzle(object):
  """
  Represant the game. Contain a population of each and get One fitnessValue.
  """
  # Constructor
  def __init__(self, lines):
    seed = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    user = getpass.getuser()
    self.personal_path = "gen/%s_%s/" % (user, seed)
    create_subdir(self.personal_path)
    self.index_line = 0
    print "Personal Path used for this Puzzle: %s" % self.personal_path

    self.completion = 0.0 # current puzzle completion in percentage

    self.toolbox = base.Toolbox()
    # Creation des deux valeurs
    creator.create("FitnessInd", base.Fitness, weights=(0,))
    creator.create("FitnessGroup", base.Fitness, weights=(0,))
    # Individu creation
    creator.create("Individual", ind.Ind, fitness_ind=creator.FitnessInd, fitness_group=creator.FitnessGroup)

    # Pseudo random. put corners at corners and border at border
    arr = list(self.randomize_lines(*lines))

    self.toolbox.register("new_individual", creator.Individual, self._get_line_, arr)
    self.toolbox.register("desk", tools.initRepeat, list, self.toolbox.new_individual)
    self.population = self.toolbox.desk(n=len(arr))
    # Applying rotation until it's the right side
    self.fixing_outside()
    # Init the stats we want to log
    self.init_stats()

  def init_stats(self):
    """
    We have to talk about it here and see what's we're looging and if we do us a math on it.
    :return:
    """
    self.stats = tools.Statistics(key=lambda ind: ind.fitness_ind.value)
    # Look for multistats if we wants stat on fitness_group
    # self.stats = tools.Statistics(key=lambda ind: ind.fitness_group.value)
    self.stats.register("avg", statistics.mean)
    self.stats.register("std", numpy.std)
    self.stats.register("min", min)
    self.stats.register("max", max)
    self.stats.register("median", statistics.median)
    self.logbook = tools.Logbook()
#    self.logbook.header = "generation", "fitness", "min", "avg", "max"
    self.record = None

  def evaluate(self):
    """

    :return:
    """
    # individuals, individual's clusters, and puzzle completion evaluations
    individuals_s, individuals_clusters_s, puzzle_completion = eval.eval_solution(self.population)

    # print "individuals evaluation:"
    # for index in range(0, 16):
    #   print individuals_s[index * 16: (index * 16) + 16]
    # print

    # print "individuals clusters evaluation:"
    # for index in range(0, 16):
    #   print individuals_clusters_s[index * 16: (index * 16) + 16]
    # print

    # print "puzzle completion:", puzzle_completion, "%\n"

    self.completion = puzzle_completion
    for individual, individual_s, cluster_s in zip(self.population, individuals_s, individuals_clusters_s):
      individual.fitness_ind.values = (individual_s,)
      individual.fitness_group.values = (individuals_clusters_s,)
    return

  #####################
  #  Tools function   #
  #####################
  def fixing_outside(self):
    for index, mask in zip(CORNER_POS, MASK_CORNERS):
      self.fit_to_border(self.population[index], mask)
    for index in BORDER_BOT:
      self.fit_to_border(self.population[index], MASK_BOT)
    for index in BORDER_TOP:
      self.fit_to_border(self.population[index], MASK_TOP)
    for index in BODER_LEFT:
      self.fit_to_border(self.population[index], MASK_LEFT)
    for index in BORDER_RIGHT:
      self.fit_to_border(self.population[index], MASK_RIGHT)

  def fit_to_border(self, ind, type):
    """
      Rotate the pieces until it feet with the border.
    :param ind:
    :param type: list of None and 0 for direction to fit.
    :return:
    """
    while not ind.mask(type):
      ind.rotate()

  def give_random_pos(self, pos, line):
    r = []
    for x in range(0, len(pos)):
      rp =  random.randrange(0, len(pos))
      rl = random.randrange(0, len(line))
      r.append((pos.pop(rp),line.pop(rl)))
    return r

  def randomize_lines(self, lc, lb, li):
    """
      Trying to have an half randomize algorithm
    :return:
    """
    lc = self.give_random_pos(copy.copy(CORNER_POS), lc)
    lb = self.give_random_pos(copy.copy(BORDER_POS), lb)
    li = self.give_random_pos(copy.copy(INSIDE_POS), li)
    l = lc + lb + li
    f = lambda lst, index, c: lst[c][1] if lst[c][0] == index else f(lst, index, c + 1)
    for x in xrange(0, 256):
      yield f(l, x, 0)

  def log_stats(self, generation):
    # Compiling the stats we ask in self.init_stats()
    self.record = self.stats.compile(self.population)
    # Writting them in the logbook Instance
    self.logbook.record(generations=generation, **self.record)
    # I case we need to keep famous big scores.
    # self.famous.update(self.pop)

  def __len__(self):
    return len(self.content)

  def __repr__(self):
    return repr(self.uid) + repr(self.population)

  def generate_graph_values(self, ngen=0):
    """
      Generate a graph and save it.
    :param ngen:
    :return:
    """
    nrow = [0, None, -1.0, 1.0]
    #[-100, -75, -50, -25, 0, 25, 50, 75, 100]

    # Temporary fix until we now exactly what we want to log
    fitnesses = range(0, 256)
    y = 0
    for x in fitnesses:
      plt.scatter(y, x, marker='.', c='c')
      y += 1
    plt.axis(nrow)
    plt.ylabel("weight")
    plt.xlabel("population")
    plt.gcf().set_size_inches(15, 5)
    plt.savefig("%s/g_%s.png" % (self.personal_path, ngen), bbox_inches='tight', dpi=100)
    plt.clf()
    plt.close()

  def _get_line_(self, arr):
    i = self.index_line
    self.index_line += 1
    return arr[i]

  def save_picture(self, gen=0, score=0):
    eternity.save(self.population, "%s/gen_%s_score_%s" % (self.personal_path, gen, score))

  def draw(self):
    eternity.draw(self.population)

  def write_logbook(self):
    with open("%s/logbook.txt" % self.personal_path, "w") as f:
      f.write(str(self.logbook))


def create_subdir(s):
  try:
    os.mkdir(s)
  except Exception as e:
    print e


if __name__ == '__main__':
  import ind
  inds = ind.get_population()
  corner = [i for i in inds if i[1].count(0) == 2]
  border = [i for i in inds if i[1].count(0) == 1]
  inside = [i for i in inds if i[1].count(0) == 0]
  puzzle = Puzzle((corner, border, inside))
  puzzle.draw()
#  puzzle.save_picture()
