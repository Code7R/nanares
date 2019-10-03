NAdroid App Restorer
====================

INSTALLATION:
------------

```
$ apt install android-sdk-build-tools python3-dialog
$ python3 nanares.py -h
```

ABOUT:
-----

Small script hacked together to make a one-time job but with comfort!

It's main purpose is to assist a simple update of a modern Android phone (Android 8 to Android 9 aka LineageOS 15 to 16).
That's done by injecting apps and their data from an existing TWRP (NAndroid) backup set.

It might support older Android versions but it's not explicitly tested.

Unless configured by options (see --help), it will assume that data is either already pulled from the phone (and then specified by the first parameter) or it will interact via dialog tool to select an existing backup.

The python version expected here is 3.7.3. It might work with Python 3.5 or even 3.3 but it's not explicitly tested.

THIS TOOL COMES WITHOUT ANY WARRANTIES!
It might damage your phone and make it unbootable!
It requires you to root the phone at least for the time of restore operation!
YOU HAVE BEEN WARNED!

```
Copyright (c) 2019 Eduard Bloch

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
