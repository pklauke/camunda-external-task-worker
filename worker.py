# -*- coding: utf-8 -*-

import typing

import pycamunda.externaltask
import pycamunda.variable


class ExternalTaskException(Exception):
    def __init__(
        self, *args, message: str, details: str = '', retry_timeout: int = 10000, **kwargs
    ):
        """Exception to be raised when a service task fails.

        :param message: Error message that describes the reason of the failure.
        :param details: Error description.
        :param retry_timeout: Timeout in milliseconds until the external task becomes available.
        """
        super().__init__(*args, **kwargs)
        self.message = message
        self.details = details
        self.retry_timeout = retry_timeout


class Worker:

    def __init__(
        self,
        url: str,
        worker_id: str,
        max_tasks: int = 1,
        async_response_timeout: int = 5000
    ):
        """Worker that fetches and completes external Camunda service tasks.

        :param url: Camunda Rest engine URL.
        :param worker_id: Id of the worker.
        :param max_tasks: Maximum number of tasks the worker fetches at once.
        :param async_response_timeout: Long polling in milliseconds.
        """
        self.fetch_and_lock = pycamunda.externaltask.FetchAndLock(
            url, worker_id, max_tasks, async_response_timeout=async_response_timeout
        )
        self.complete_task = pycamunda.externaltask.Complete(
            url, id_=None, worker_id=worker_id
        )
        self.handle_failure = pycamunda.externaltask.HandleFailure(
            url,
            id_=None,
            worker_id=worker_id,
            error_message='',
            error_details='',
            retries=0,
            retry_timeout=0
        )

        self.stopped = False
        self.topic_funcs = {}

    def subscribe(
        self,
        topic: str,
        func: typing.Callable,
        lock_duration: int = 10000,
        variables: typing.Iterable[str] = None,
        deserialize_values: bool = False
    ):
        """Subscribe the worker to a certain topic.

        :param topic: The topic to subscribe to.
        :param func: The callable that is executed for a task of the respective topic.
        :param lock_duration: Duration the fetched tasks are locked for this worker in milliseconds.
        :param variables: Variables to request from the Camunda process instance.
        :param deserialize_values: Whether serializable variables values are deserialized on server
                                   side.
        """
        self.fetch_and_lock.add_topic(topic, lock_duration, variables, deserialize_values)
        self.topic_funcs[topic] = func

    def unsubscribe(self, topic):
        """Unsubscribe the worker from a topic.

        :param topic: The topic to unsubscribe from.
        """
        for i, topic_ in enumerate(self.fetch_and_lock.topics):
            if topic_['topicName'] == topic:
                del self.fetch_and_lock.topics[i]
                break

    def run(self):
        """Run the worker."""
        while not self.stopped:
            tasks = self.fetch_and_lock()

            for task in tasks:
                try:
                    return_variables = self.topic_funcs[task.topic_name](**task.variables)
                except ExternalTaskException as exc:
                    self.handle_failure.id_ = task.id_
                    self.handle_failure.error_message = exc.message
                    self.handle_failure.error_details = exc.details
                    self.handle_failure.retry_timeout = exc.retry_timeout
                    if task.retries is None:
                        self.handle_failure.retries = 3
                    else:
                        self.handle_failure.retries = task.retries - 1
                    self.handle_failure()
                else:
                    self.complete_task.variables = {}
                    self.complete_task.id_ = task.id_
                    for variable, value in return_variables.items():
                        self.complete_task.add_variable(name=variable, value=value)
                    self.complete_task()
