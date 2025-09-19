from AnonMusic.core.bot import Anony
from AnonMusic.core.dir import dirr
from AnonMusic.core.git import git
from AnonMusic.core.userbot import Userbot
from AnonMusic.misc import heroku, dbb

from .logging import LOGGER

dirr()
git()
dbb()
heroku()

app = Anony()
userbot = Userbot()

from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
