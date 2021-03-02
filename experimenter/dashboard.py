import subprocess
import time
import webbrowser

from experimenter import config


def connect() -> None:
    redis_config = config.RedisConfig()
    redis_url = 'redis://{host}:{port}'.format(host=redis_config.host, port=redis_config.port)
    dashboard_url = 'http://0.0.0.0:{port}'.format(port=redis_config.dashboard_port)

    dashboard_args = [
        'rq-dashboard', '--port', str(redis_config.dashboard_port),
        '--redis-url', redis_url,
    ]
    dashboard_process = subprocess.Popen(dashboard_args)
    time.sleep(1)
    
    webbrowser.open(dashboard_url, new=1)
    dashboard_process.communicate()
