from hw8 import WaitsForGraphTracker, Action

wfgt = WaitsForGraphTracker()
self.assertEqual({}, wfgt.get_current_graph())

remaining_actions = wfgt.add_action(Action("Table_A", "trans_Josh", "REQUEST_LOCK"))
self.assertEqual([], remaining_actions)
self.assertEqual({}, wfgt.get_current_graph())

remaining_actions = wfgt.add_action(Action("Table_B", "trans_Emily", "REQUEST_LOCK"))
self.assertEqual([], remaining_actions)
self.assertEqual({}, wfgt.get_current_graph())

remaining_actions = wfgt.add_action(Action("Table_B", "trans_Josh", "REQUEST_LOCK"))
self.assertEqual([Action("Table_B", "trans_Josh", "REQUEST_LOCK")], remaining_actions)
self.assertEqual({"trans_Josh": "trans_Emily"}, wfgt.get_current_graph())

remaining_actions = wfgt.add_action(Action("Table_B", "trans_Emily", "REQUEST_LOCK"))
self.assertEqual([Action("Table_B", "trans_Josh", "REQUEST_LOCK")], remaining_actions)
self.assertEqual({"trans_Josh": "trans_Emily"}, wfgt.get_current_graph())

remaining_actions = wfgt.add_action(Action("Table_C", "trans_Josh", "REQUEST_LOCK"))
self.assertEqual([
    Action("Table_B", "trans_Josh", "REQUEST_LOCK"),
    Action("Table_C", "trans_Josh", "REQUEST_LOCK"),
    ], remaining_actions)
self.assertEqual({"trans_Josh": "trans_Emily"}, wfgt.get_current_graph())