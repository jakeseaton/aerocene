# are we debugging locally or running
# on the delopment instance
import os
DEBUG = os.environ['STAGE'] == 'dev'