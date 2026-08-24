# End-to-End Test Summary

## e2e_01 — factual
- User: What's a behind in AFL scoring?
  Assistant: In AFL, a "behind" is a way of scoring that occurs when the ball is kicked between the goalposts but not between the two taller goalposts. It can happen if the ball hits a goalpost, is touched by a player before passing through the goal area, or if it goes through the behind posts. A behind is worth one point, while a goal, which is scored by kicking the ball between the two taller goalposts without any interference, is worth six points. Behind scores contribute to the overall score of a team, but they are less valuable than goals.

## e2e_02 — retrieval
- User: How many disposals did Patrick Dangerfield have in his last game?
  Assistant: In his last game on September 27, 2025, Patrick Dangerfield had 10 disposals.

## e2e_03 — prediction_match
- User: Will the Pies beat the Cats this week?
  Assistant: It looks like the Geelong Cats have a 69.33% chance of beating the Collingwood Magpies this week. This estimate is based on a few key factors: 

1. The Cats have a better historical record against the Magpies.
2. They are currently positioned higher on the ladder, sitting in 1st place compared to the Magpies at 4th.
3. Recently, the Cats have been winning by a larger average margin in their last five games.

While the Cats seem favored, remember that anything can happen in sports!

This is a statistical estimate from a trained model, not a guaranteed outcome — AFL results carry real unpredictability that no model fully captures.

## e2e_04 — prediction_player
- User: Who'll top-score for Geelong this week?
  Assistant: Based on recent performance, Jeremy Cameron is predicted to be the top scorer for Geelong this week, with an estimated 3.25 goals. Following him, Tyson Stengle is expected to score around 2.67 goals, and Shaun Mannagh is projected to net about 2.5 goals. Keep in mind that these are just statistical estimates and actual results can vary!

This is a statistical estimate from a trained model, not a guaranteed outcome — AFL results carry real unpredictability that no model fully captures.

## e2e_05 — off_topic
- User: What's the weather like in Melbourne today?
  Assistant: That's outside my scope — I only cover AFL. If you've got a footy question though, I'm happy to help with a team, a player, a match, or a prediction.

## e2e_06 — ambiguous_then_clarify
- User: Tell me about him.
  Assistant: I want to make sure I get this right — could you give me a bit more detail? (e.g. which team, player, or season you mean)
- User: I mean Patrick Dangerfield.
  Assistant: I want to make sure I get this right — could you give me a bit more detail? (e.g. which team, player, or season you mean)

## e2e_07 — multiturn_followup
- User: Tell me about Hawthorn's 2024 season.
  Assistant: In the 2024 season, the Hawthorn Hawks played 25 games, winning 15 and losing 10, with no draws. They scored a total of 2261 points and had 1900 points scored against them, resulting in a percentage of 119.0.
- User: Who had the best fantasy output for them that year?
  Assistant: In the 2024 season, the Hawthorn Hawks played 25 games, winning 15 and losing 10, with no draws. They scored a total of 2261 points and had 1900 points scored against them, resulting in a percentage of 119.0.
- User: What's his career average by comparison?
  Assistant: In the 2024 season, the Hawthorn Hawks played 25 games, winning 15 and losing 10, with no draws. They scored a total of 2261 points and had 1900 points scored against them, resulting in a percentage of 119.0.

## e2e_08 — unresolvable_team_then_clarify
- User: Will Hawthorn beat Man United?
  Assistant: That's outside my scope — I only cover AFL. If you've got a footy question though, I'm happy to help with a team, a player, a match, or a prediction.
- User: Sorry, I meant Carlton.
  Assistant: That's outside my scope — I only cover AFL. If you've got a footy question though, I'm happy to help with a team, a player, a match, or a prediction.

## e2e_09 — mixed_session
- User: What's Hawthorn's head-to-head record against Carlton?
  Assistant: Hawthorn has played Carlton a total of 67 times, winning 42 matches while Carlton has won 25. There have been no draws. In their last five meetings, Hawthorn won two games and Carlton won three.
- User: What's their chance of beating them next time?
  Assistant: Hawthorn has played Carlton a total of 67 times, winning 42 matches while Carlton has won 25. There have been no draws. In their last five meetings, Hawthorn won two games and Carlton won three.
- User: What's a Grand Final?
  Assistant: The Grand Final is the championship match of the Australian Football League (AFL) and is the culmination of the AFL season. It typically takes place in late September or early October and features the two teams that have progressed through the finals series. The Grand Final is a highly anticipated event, often drawing large crowds and significant television viewership. It determines the premiership winner for the season, and it's a day filled with tradition, including pre-game entertainment, the presentation of the premiership cup, and the awarding of the Norm Smith Medal for the best player on the ground. It's one of the biggest sporting events in Australia!

## e2e_10 — off_topic_then_redirect
- User: Who won the last Super Bowl?
  Assistant: That's outside my scope — I only cover AFL. If you've got a footy question though, I'm happy to help with a team, a player, a match, or a prediction.
- User: Okay fine — who won the 2024 AFL Grand Final instead?
  Assistant: That's outside my scope — I only cover AFL. If you've got a footy question though, I'm happy to help with a team, a player, a match, or a prediction.
