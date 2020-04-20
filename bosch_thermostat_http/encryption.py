"""Encryption logic of Bosch thermostat."""
import base64
import hashlib
import binascii
import json

from pyaes import PADDING_NONE, AESModeOfOperationECB, Decrypter, Encrypter

from .const import BS, MAGIC_HTTP, MAGIC_XMPP
from .exceptions import EncryptionException, DeviceException





class Encryption:
    """Encryption class."""

    def __init__(self, access_key, device_type="IVT", password=None):
        """
        Initialize encryption.

        :param str access_key: Access key to Bosch thermostat.
            If no password specified assumed as ready key to encrypt.
        :param str password: Password created with Bosch app.
        """
        self._bs = BS
        magic = MAGIC_HTTP if device_type.upper() == "IVT" else MAGIC_XMPP
        if password and access_key:
            key_hash = hashlib.md5(bytearray(access_key, "utf8") + magic)
            password_hash = hashlib.md5(magic + bytearray(password, "utf8"))
            self._saved_key = key_hash.hexdigest() + password_hash.hexdigest()
            self._key = binascii.unhexlify(self._saved_key)
        elif access_key:
            self._saved_key = access_key
            self._key = binascii.unhexlify(self._saved_key)

    @property
    def key(self):
        """Return key to store in config entry."""
        return self._saved_key

    def json_encrypt(self, raw):
        try:
            if raw:
                return json.loads(self.decrypt(raw))
            return None
        except json.JSONDecodeError:
            raise DeviceException(f"Unable to decode Json response.")

    def encrypt(self, raw):
        """Encrypt raw message."""
        if len(raw) % self._bs != 0:
            raw = self._pad(raw)
        cipher = Encrypter(
            AESModeOfOperationECB(self._key),
            padding=PADDING_NONE)
        ciphertext = cipher.feed(raw) + cipher.feed()
        return base64.b64encode(ciphertext)

    def decrypt(self, enc):
        """
        Decryption algorithm.

        Decrypt raw message only if length > 2.
        Padding is not working for lenght less than 2.
        """
        try:
            if enc and len(enc) > 2:
                enc = base64.b64decode(enc)
                if len(enc) % self._bs != 0:
                    enc = self._pad(enc)
                cipher = Decrypter(
                    AESModeOfOperationECB(self._key),
                    padding=PADDING_NONE)
                decrypted = cipher.feed(enc) + cipher.feed()
                return decrypted.decode("utf8").rstrip(chr(0))
            return "{}"
        except Exception as err:
            raise EncryptionException(f"Unable to decrypt: {err}")

    def _pad(self, _s):
        """Pad of encryption."""
        return _s + ((self._bs - len(_s) % self._bs) * chr(0))
