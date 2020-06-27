# -*- coding: utf-8 -*-

import random
import typing

import pycamunda.variable

import worker


def generate_random_number(
        range_min: pycamunda.variable.Variable, range_max: pycamunda.variable.Variable
) -> typing.Dict[str, int]:
    try:
        number = random.randrange(range_min.value, range_max.value)
    except ValueError:
        raise worker.ExternalTaskException(message='invalid input')

    return {'number': number}


def print_number(number: pycamunda.variable.Variable) -> typing.Dict:
    print('Generated random number:', number)

    return {}


if __name__ == '__main__':
    import pycamunda.processdef

    url = 'http://localhost:8080/engine-rest'
    worker_id = '1'

    start_instance = pycamunda.processdef.StartInstance(url=url, key='randomNumberProcess')
    start_instance.add_variable(name='range_min', value=0)
    start_instance.add_variable(name='range_max', value=100)

    for _ in range(3):
        start_instance()

    worker = worker.Worker(url=url, worker_id=worker_id)
    worker.subscribe(
        topic='randomNumberTopic',
        func=generate_random_number,
        variables=['range_min', 'range_max']
    )
    worker.subscribe(
        topic='printNumberTopic',
        func=print_number,
        variables=['number']
    )

    worker.run()
