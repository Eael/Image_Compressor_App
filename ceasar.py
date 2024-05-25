#!/usr/bin/env python3

def encrypt(shift, word):
    encrypted_word = ""
    for i in range(len(word)):
      try:
          char = word[i]
          if (char.isupper()):
              encrypted_word += chr((ord(char) + shift-65) % 26 + 65)
          else:
              encrypted_word += chr((ord(char) + shift-97) % 26 + 97)

      except IndexError:
          print ("Word out of range")

    return encrypted_word

def decrypt(encrypted_word,shift):
    decrypted_word = ""
    for i in range(len(encrypted_word)):
      char = encrypted_word[i]
      if (char.isupper()):
          decrypted_word += chr((ord(char) + 26 - (shift - 65)) % 26 + 65)
      else:
          decrypted_word += chr((ord(char) + 26 - (shift + 97)) % 26 + 97)
    return decrypted_word

word = "Earl Felix"
shift = 4

print ("Plain Text : " + word)
print ("Shift pattern : " + str(shift))
print ("Cipher: " + encrypt(shift, word))
print ("Decrypt: " + decrypt(encrypt(shift,word), shift))
