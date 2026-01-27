import time
from opentelemetry import trace

def func1_sub(tracer):
    with tracer.start_as_current_span("func1_sub"):
        print ("Hello")
        time.sleep(1)

def func1(tracer):
    with tracer.start_as_current_span("func1"):
        i = 0
        while i < 3:
            func1_sub(tracer)
            i += 1

if __name__ == "__main__":
    tracer = trace.get_tracer(__name__)

    func1(tracer)
