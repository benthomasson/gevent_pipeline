#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `gevent_pipeline` package."""


import unittest

from gevent_pipeline.fsm import Channel, FSMController, State


class TestChannel(unittest.TestCase):

    def test_put(self):
        channel = Channel(None, None, None)
        channel.put(['foo', {}])

    def test_put_get(self):
        channel = Channel(None, None, None)
        channel.put(['foo', {}])
        assert channel.get(block=False)


class _AState(State):

    pass


AState = _AState()


class TestFSMController(unittest.TestCase):

    def test_init(self):
        FSMController({}, 'test', AState, self)
