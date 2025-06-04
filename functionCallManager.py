"""
Manages registered function calls dispatched in
parallel with full result marshalling.

Makes function calls in either a threading or multiprocessing
worker based on thread-safety annotations.
"""
import typing
import time
import threading
import multiprocessing
from multiprocessing.connection import PipeConnection
import queue
import uuid
import traceback


class FunctionCallManager:
    """
    Manages registered function calls dispatched in
    parallel with full result marshalling.

    Makes function calls in either a threading or multiprocessing
    worker based on thread-safety annotations.
    """

    def __init__(self,num_threads:int=4,num_processes:int=2)->None:
        self.functions:typing.Dict[
            str,
            typing.Tuple[typing.Callable[...,typing.Any],bool]]={}
        self.threadsafe_queue:queue.Queue=queue.Queue()
        self.multiproc_queue:multiprocessing.Queue=multiprocessing.Queue()
        self.results:typing.Dict[
            str,
            typing.Tuple[typing.Any,typing.Optional[Exception]]]={}
        self.result_events:typing.Dict[
            str,
            typing.Union[threading.Event,multiprocessing.Event]]={}
        self.lock=threading.Lock()
        self.num_threads=num_threads
        self.num_processes=num_processes
        self._shutdown_event=threading.Event()
        self._processes:typing.List[multiprocessing.Process]=[]
        self._threads:typing.List[threading.Thread]=[]
        self._collector_thread:typing.Optional[threading.Thread]=None
        self.parent_conns:typing.List[PipeConnection]=[]
        self.start()

    def start(self)->None:
        """
        Start all threads and processes
        """
        self._start_thread_workers()
        self._start_process_workers()

    def stop(self)->None:
        """
        Stop all threads/processes
        """
        self._shutdown_event.set()
        for _ in range(self.num_threads):
            self.threadsafe_queue.put(None)
        for _ in range(self.num_processes):
            self.multiproc_queue.put(None)
        for t in self._threads:
            t.join()
        if self._collector_thread:
            self._collector_thread.join()
        for p in self._processes:
            p.join()
        for conn in self.parent_conns:
            conn.close()
        self._threads.clear()
        self._processes.clear()
        self.parent_conns.clear()
    def __del__(self):
        self.stop()

    def addFunction(self,
        func:typing.Callable[...,typing.Any],
        name:typing.Optional[str]=None,
        threadsafe:bool=False)->None:
        """
        Registers a function with a name and whether it is threadsafe.

        :param name: Unique name for the function
        :param func: Callable function to register
        :param threadsafe: Boolean indicating if the function
            is safe to call from threads
        """
        if name is None:
            name=func.__name__
        self.functions[name]=(func,threadsafe)

    def call(self,
        name:str,
        *args:typing.List[typing.Any],
        **kwargs:typing.Dict[str,typing.Any]
        )->typing.Any:
        """
        Calls a registered function asynchronously,
        blocking until result or exception is returned.

        :param name: Name of the function to call
        :param args: Positional arguments for the function
        :param kwargs: Keyword arguments for the function
        :return: Return value from the function
        :raises Exception: Any exception raised inside the target function
        """
        if name not in self.functions:
            raise ValueError(f"Function '{name}' is not registered.")
        func,threadsafe=self.functions[name]
        call_id=str(uuid.uuid4())
        event=threading.Event() if threadsafe else multiprocessing.Event()
        with self.lock:
            self.result_events[call_id]=event
        call_data={'id':call_id,'func':func,'args':args,'kwargs':kwargs}
        if threadsafe:
            self.threadsafe_queue.put(call_data)
        else:
            self.multiproc_queue.put(call_data)
        event.wait()
        with self.lock:
            result,exception=self.results.pop(call_id)
            self.result_events.pop(call_id)
        if exception:
            raise exception
        return result
    __call__=call

    def _start_thread_workers(self)->None:
        """
        Starts the threading-based workers.
        """
        def thread_worker()->None:
            """
            One of any number of thread workers
            """
            while not self._shutdown_event.is_set():
                try:
                    call_data=self.threadsafe_queue.get(timeout=0.1)
                except queue.Empty:
                    try:
                        call_data=self.multiproc_queue.get_nowait()
                    except queue.Empty:
                        continue
                if call_data is None:
                    break
                call_id=call_data['id']
                func=call_data['func']
                args=call_data['args']
                kwargs=call_data['kwargs']
                try:
                    result=func(*args,**kwargs)
                    exception=None
                except Exception as e:
                    result=None
                    exception=e
                with self.lock:
                    self.results[call_id]=(result,exception)
                    event=self.result_events[call_id]
                    event.set()
        for _ in range(self.num_threads):
            t=threading.Thread(target=thread_worker,daemon=True)
            t.start()
            self._threads.append(t)

    def _start_process_workers(self)->None:
        """
        Starts the multiprocessing-based workers.
        """
        self.parent_conns=[]
        def process_worker(
            task_queue:multiprocessing.Queue,
            conn:multiprocessing.connection.Connection
            )->None:
            """
            One of any number of process workers
            """
            while True:
                call_data=task_queue.get()
                if call_data is None:
                    break
                call_id=call_data['id']
                func=call_data['func']
                args=call_data['args']
                kwargs=call_data['kwargs']
                try:
                    result=func(*args,**kwargs)
                    conn.send((call_id,result,None))
                except Exception:
                    conn.send((call_id,None,traceback.format_exc()))
        for _ in range(self.num_processes):
            parent_conn,child_conn=multiprocessing.Pipe()
            proc=multiprocessing.Process(
                target=process_worker,
                args=(self.multiproc_queue,child_conn),
                daemon=True)
            proc.start()
            self.parent_conns.append(parent_conn)
            self._processes.append(proc)
        def collect_results()->None:
            while not self._shutdown_event.is_set():
                for conn in self.parent_conns:
                    if conn.poll():
                        call_id,result,exc_info=conn.recv()
                        exception:typing.Optional[RuntimeError]=None
                        if exc_info:
                            exception=RuntimeError(
                                f"Exception in subprocess:\n{exc_info}")
                        with self.lock:
                            self.results[call_id]=(result,exception)
                            event=self.result_events[call_id]
                            event.set()
                time.sleep(0.01)
        self._collector_thread=threading.Thread(
            target=collect_results,daemon=True)
        self._collector_thread.start()
