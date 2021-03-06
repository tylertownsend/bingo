# Ignoring some linting rules in tests
# pylint: disable=redefined-outer-name
# pylint: disable=missing-docstring
import random

import pytest
import numpy as np

from bingo.Base.MultipleValues import SinglePointCrossover, \
                                      SinglePointMutation, \
                                      MultipleValueChromosomeGenerator
from bingo.Base.Island import Island
from bingo.Base.MuPlusLambdaEA import MuPlusLambda
from bingo.Base.TournamentSelection import Tournament
from bingo.Base.Evaluation import Evaluation
from bingo.Base.FitnessFunction import FitnessFunction
from bingo.Base.SerialArchipelago import SerialArchipelago


POP_SIZE = 5
SELECTION_SIZE = 10
VALUE_LIST_SIZE = 10
OFFSPRING_SIZE = 20
ERROR_TOL = 10e-6


class MultipleValueFitnessFunction(FitnessFunction):
    def __call__(self, individual):
        fitness = np.count_nonzero(individual.values)
        self.eval_count += 1
        return fitness


def generate_three():
    return 3


def generate_two():
    return 2


def generate_one():
    return 1


def generate_zero():
    return 0


def mutation_function():
    return np.random.choice([False, True])


@pytest.fixture
def evol_alg():
    crossover = SinglePointCrossover()
    mutation = SinglePointMutation(mutation_function)
    selection = Tournament(SELECTION_SIZE)
    fitness = MultipleValueFitnessFunction()
    evaluator = Evaluation(fitness)
    return MuPlusLambda(evaluator, selection, crossover, mutation,
                        0.2, 0.4, OFFSPRING_SIZE)


@pytest.fixture
def zero_island(evol_alg):
    generator = MultipleValueChromosomeGenerator(generate_zero,
                                                 VALUE_LIST_SIZE)
    return Island(evol_alg, generator, POP_SIZE)


@pytest.fixture
def one_island(evol_alg):
    generator = MultipleValueChromosomeGenerator(generate_one,
                                                 VALUE_LIST_SIZE)
    return Island(evol_alg, generator, POP_SIZE)


@pytest.fixture
def two_island(evol_alg):
    generator = MultipleValueChromosomeGenerator(generate_two,
                                                 VALUE_LIST_SIZE)
    return Island(evol_alg, generator, POP_SIZE)


@pytest.fixture
def three_island(evol_alg):
    generator = MultipleValueChromosomeGenerator(generate_three,
                                                 VALUE_LIST_SIZE)
    return Island(evol_alg, generator, POP_SIZE)


@pytest.fixture
def island_list(zero_island, one_island, two_island, three_island):
    return [zero_island, one_island, two_island, three_island]


@pytest.fixture
def island(evol_alg):
    generator = MultipleValueChromosomeGenerator(mutation_function,
                                                 VALUE_LIST_SIZE)
    return Island(evol_alg, generator, POP_SIZE)


def test_archipelago_generated(island):
    archipelago = SerialArchipelago(island, num_islands=3)
    assert len(archipelago._islands) == 3
    for island_i in archipelago._islands:
        assert island_i != island
        assert island_i._population_size == island._population_size


def test_generational_step_executed(island):
    random.seed(0)
    archipelago = SerialArchipelago(island, num_islands=3)
    archipelago.step_through_generations(1)
    for island_i in archipelago._islands:
        assert island_i.best_individual()


def test_island_migration(one_island, island_list):
    archipelago = SerialArchipelago(one_island, num_islands=4)
    archipelago._islands = island_list

    archipelago.coordinate_migration_between_islands()

    migration_count = 0
    for i, island in enumerate(archipelago._islands):
        initial_individual_values = [i]*VALUE_LIST_SIZE
        for individual in island.population:
            if initial_individual_values != individual.values:
                migration_count += 1
                break
    assert len(island_list) == migration_count


def test_convergence_of_archipelago(one_island, island_list):
    archipelago = SerialArchipelago(one_island, num_islands=4)
    archipelago._islands = island_list

    converged = archipelago.test_for_convergence(0)
    assert converged


def test_convergence_of_archipelago_unconverged(one_island):
    archipelago = SerialArchipelago(one_island, num_islands=6)
    converged = archipelago.test_for_convergence(0)
    assert not converged


def test_assign_and_receive(one_island, two_island):
    send, receive = \
                SerialArchipelago.assign_send_receive(one_island, two_island)
    for s, r in zip(send, receive):
        assert 0 <= s < len(one_island.population) <= len(two_island.population)
        assert 0 <= r < len(one_island.population) <= len(two_island.population)

def test_best_individual_returned(one_island):
    generator = MultipleValueChromosomeGenerator(generate_zero, VALUE_LIST_SIZE)
    best_indv = generator()
    one_island.load_population([best_indv], replace=False)
    archipelago = SerialArchipelago(one_island)
    assert archipelago.test_for_convergence(error_tol=ERROR_TOL)
    assert archipelago.get_best_individual().fitness == 0


def test_archipelago_runs(one_island, two_island, three_island):
    max_generations = 100
    min_generations = 20
    error_tol = 0
    generation_step_report = 10
    archipelago = SerialArchipelago(one_island, num_islands=4)
    archipelago._islands = [one_island, two_island, three_island, three_island]
    converged = archipelago.run_islands(max_generations,
                                        min_generations,
                                        generation_step_report,
                                        error_tol)
    assert converged