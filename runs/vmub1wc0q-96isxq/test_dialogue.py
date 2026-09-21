import unittest
from dialogue_system import Blackboard, AttributeCondition, ItemCondition, QuestCondition, DialogueOption, DialogueNode

class TestDialogueArchitecture(unittest.TestCase):
    def setUp(self):
        self.bb = Blackboard()
        self.bb.set("strength", 10)
        self.bb.set("inventory", ["sword"])
        self.bb.set("completed_quests", ["q1"])

    def test_attribute_condition(self):
        cond_pass = AttributeCondition("strength", 5)
        cond_fail = AttributeCondition("strength", 15)
        self.assertTrue(cond_pass.is_met(self.bb))
        self.assertFalse(cond_fail.is_met(self.bb))

    def test_item_condition(self):
        cond_pass = ItemCondition("sword")
        cond_fail = ItemCondition("shield")
        self.assertTrue(cond_pass.is_met(self.bb))
        self.assertFalse(cond_fail.is_met(self.bb))

    def test_quest_condition(self):
        cond_pass = QuestCondition("q1")
        cond_fail = QuestCondition("q2")
        self.assertTrue(cond_pass.is_met(self.bb))
        self.assertFalse(cond_fail.is_met(self.bb))

    def test_decoupling_logic(self):
        # O teste crucial: O sistema de diálogo não deve ter acesso ao objeto 'Player'
        # Ele só deve conseguir ler o que foi injetado no Blackboard.
        option = DialogueOption("Test", "next", [AttributeCondition("strength", 10)])
        self.assertTrue(option.is_available(self.bb))

if __name__ == "__main__":
    unittest.main()