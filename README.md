# Ablaze

A Discord library to ease bot development and improve speed of development.

## Development

Discussion around development happens in the [Ablaze Discord server](https://discord.gg/7dUjwFu2rH), which is where you should go if you wish to contribute to the project.

## Installation

Ablaze is in a very early stage right now, as such the code is not on PyPI, but can still be installed by running:

- Linux/Mac: `pip3 install git+https://github.com/vcokltfre/ablaze`
- Windows: `py -m pip install git+https://github.com/vcokltfre/ablaze`

## Design Methodology

Ablaze is designed with one primary core value in mind: it should be easy to use, and easy to understand.

### What does this mean?

Essentially, there shouldn't be any 'sharp corners' that people get stuck on because they are weird or don't conform to what's expected. Consistency is key to simplicity. Let's say, for example, we have the classes `Channel` and `User`, both of which have a `send()` method to send a message. It would make little sense, given that context, to name the name method on a `Webhook` object something like `send_message()`.

There will, as with anything, be things that are not intuitively understood by everyone using the library, and for that reason this section exists, to clarify exactly what the library does, how, and why.

### Caching

All cache methods:

- are `synchronous`, meaning you do not await them.
- have an O(1) access time, as they fetch from a `dict`.
- will return `None` if the item is not found during a get call. They will not raise an exception if an item is not found.
- will accept only integer keys. If a non-`int` key is provided as a key a TypeError will be raised.

For example:

```py
# Assume `cache` is a channel cache.
# Assume the channel with the ID `1234` is in the cache.

cache.get(1234)  # Returns the channel object.
cache.get(4321)  # Returns None.
cache.get("1234")  # Raises TypeError.
```

Setting an object in the cache is done by calling `cache.set(key, value)`.

### API objects

API objects include classes such as `Message`, `Channel`, `Guild`, etc. These objects are essentially a way to view a remote state; in English, they represent objects stored by Discord, locally. These objects are always immutable (frozen dataclasses). The reason for this is that there should be no need to modify the state of Discord objects without actually doing so in the API, in which case the object will be re-created and places it is cached updated with the new object.
