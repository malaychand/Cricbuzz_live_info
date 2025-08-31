import streamlit as st
import pandas as pd
import sqlite3
import sqlparse

DB_PATH = "cricket_info.db"

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def run_query(query):
    conn = get_db_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_tables():
    conn = get_db_connection()
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
    conn.close()
    return tables["name"].tolist()

def get_table_schema(table):
    conn = get_db_connection()
    schema = pd.read_sql(f"PRAGMA table_info({table});", conn)
    conn.close()
    return schema

def main():
    st.title("🏏 Cricket SQL Playground")

    # ---------------------- Predefined Queries ----------------------
    tab1, tab2 = st.tabs(["🚀 Quick Queries", "💡 Custom Query Runner"])

    with tab1:
        # NOTE: Many of the queries below assume common table/column names.
        # If your schema differs, tweak table/column names inside the SQL.
        queries = {
            # Q1
            "Q1. Players from India: full name, role, batting & bowling styles": """
                SELECT name AS full_name, playing_role, batting_style, bowling_style
                FROM players
                WHERE country = 'India';
            """,

            # Q2 
            "Q2. Matches in the last 30 days (desc)": """
                SELECT 
                    Description,
                    "Team 1" AS Team1,
                    "Team 2" AS Team2,
                    Venue_location AS Venue,
                    Venue_city AS City,
                    date("Start Date") AS Match_Date
                FROM cricket_matches_processed
                WHERE date("Start Date") >= date('now', '-30 day')
                ORDER BY date("Start Date") DESC;
            """,

            # Q3
            "Q3. Top 10 ODI run scorers (name, total runs, avg, 100s)": """
                SELECT "Player Name",
                    "Total Runs",
                    "Batting Average",
                    "Centuries"
                FROM odi_scorers
                ORDER BY "Total Runs" DESC
                LIMIT 10;
            """,

            # Q4
            "Q4. Venues with capacity > 50,000 (largest first)": """
                SELECT venue_name,
                    city,
                    country,
                    capacity
                FROM venues
                WHERE capacity > 50000
                ORDER BY capacity DESC;
            """,

            # Q5
            "Q5. Matches won by each team (most wins first)": """
                SELECT 
                    TRIM(SUBSTR(Status, 1, INSTR(Status, ' won') - 1)) AS Team_Name,
                    COUNT(*) AS Total_Wins
                FROM cricket_matches
                WHERE Status LIKE '%won%'
                GROUP BY Team_Name
                ORDER BY Total_Wins DESC;
            """,

            # Q6
            "Q6. Player counts by playing role": """
                /* Expected table: players(playing_role) */
                SELECT playing_role AS role, COUNT(*) AS player_count
                FROM players
                GROUP BY playing_role
                ORDER BY player_count DESC;
            """,

            # Q7
            "Q7. Highest individual batting score per format": """
                /* Expected tables: batting_innings(innings_id, player_id, format, runs), formats in ('Test','ODI','T20I') */
                SELECT format,
                       MAX(runs) AS highest_score
                FROM batting_innings
                WHERE format IN ('Test','ODI','T20I')
                GROUP BY format;
            """,

            # Q8
            "Q8. Series that started in 2024": """
                /* Expected table: series(series_id, series_name, host_country, match_type, start_date, total_matches) */
                SELECT series_name, host_country, match_type, start_date, total_matches
                FROM series
                WHERE strftime('%Y', start_date) = '2024'
                ORDER BY DATE(start_date);
            """,

            # Q9
            "Q9. All-rounders with >1000 runs AND >50 wickets (by format)": """
                /* Expected tables:
                   batting_totals(player_id, format, runs_total)
                   bowling_totals(player_id, format, wickets_total)
                   players(player_id, name)
                */
                SELECT p.name AS player_name, bt.format,
                       bt.runs_total AS total_runs,
                       bw.wickets_total AS total_wickets
                FROM batting_totals bt
                JOIN bowling_totals bw ON bw.player_id = bt.player_id AND bw.format = bt.format
                JOIN players p ON p.player_id = bt.player_id
                WHERE bt.runs_total > 1000 AND bw.wickets_total > 50
                ORDER BY bt.format, bt.runs_total DESC, bw.wickets_total DESC;
            """,

            # Q10
            "Q10. Last 20 completed matches (desc)": """
                /* Expected table: matches(match_id, match_title, team1, team2, winner_team, victory_margin, victory_type, venue_name, state)
                   state='Complete' or similar
                */
                SELECT match_title,
                       team1, team2,
                       winner_team,
                       victory_margin,
                       victory_type,
                       venue_name,
                       match_date
                FROM matches
                WHERE state = 'Complete'
                ORDER BY DATE(match_date) DESC, match_id DESC
                LIMIT 20;
            """,

            # Q11
            "Q11. Players with >=2 formats: runs by format + overall batting avg": """
                /* Expected tables:
                   batting_totals(player_id, format, runs_total, innings, outs, average)
                   players(player_id, name)
                */
                WITH per_format AS (
                  SELECT player_id,
                         SUM(CASE WHEN format='Test' THEN runs_total ELSE 0 END) AS test_runs,
                         SUM(CASE WHEN format='ODI'  THEN runs_total ELSE 0 END) AS odi_runs,
                         SUM(CASE WHEN format='T20I' THEN runs_total ELSE 0 END) AS t20i_runs,
                         COUNT(DISTINCT format) AS fmt_count
                  FROM batting_totals
                  GROUP BY player_id
                ),
                overall AS (
                  SELECT player_id,
                         CAST(SUM(runs_total) AS FLOAT) / NULLIF(SUM(outs),0) AS overall_batting_avg
                  FROM batting_totals
                  GROUP BY player_id
                )
                SELECT p.name,
                       pf.test_runs, pf.odi_runs, pf.t20i_runs,
                       ROUND(o.overall_batting_avg, 2) AS overall_batting_avg
                FROM per_format pf
                JOIN players p ON p.player_id = pf.player_id
                LEFT JOIN overall o ON o.player_id = pf.player_id
                WHERE pf.fmt_count >= 2
                ORDER BY overall_batting_avg DESC NULLS LAST;
            """,

            # Q12
            "Q12. Team wins at home vs away": """
                /* Expected tables:
                   matches(match_id, match_date, team1, team2, winner_team, venue_country)
                   teams(team_name, country)
                */
                WITH teams_norm AS (
                  SELECT team_name, country FROM teams
                ),
                labeled AS (
                  SELECT m.*,
                         CASE
                           WHEN m.venue_country = t1.country AND (m.team1 = t1.team_name) THEN m.team1
                           WHEN m.venue_country = t2.country AND (m.team2 = t2.team_name) THEN m.team2
                           ELSE NULL
                         END AS home_team
                  FROM matches m
                  LEFT JOIN teams_norm t1 ON t1.team_name = m.team1
                  LEFT JOIN teams_norm t2 ON t2.team_name = m.team2
                )
                SELECT team,
                       SUM(CASE WHEN team = home_team  AND winner_team = team THEN 1 ELSE 0 END) AS home_wins,
                       SUM(CASE WHEN team != home_team AND winner_team = team THEN 1 ELSE 0 END) AS away_wins
                FROM (
                  SELECT team1 AS team, * FROM labeled
                  UNION ALL
                  SELECT team2 AS team, * FROM labeled
                )
                GROUP BY team
                ORDER BY (home_wins + away_wins) DESC;
            """,

            # Q13
            "Q13. Partnerships (adjacent batters) >= 100 runs in an innings": """
                /* Expected tables:
                   batting_innings(innings_id, match_id, player_id, batting_position, runs, partnership_id)
                   partnerships(partnership_id, innings_id, runs, wicket_number)
                   players(player_id, name)
                */
                SELECT p1.name AS batter_1, p2.name AS batter_2,
                       bp.runs AS partnership_runs,
                       bi1.innings_id
                FROM partnerships bp
                JOIN batting_innings bi1 ON bi1.partnership_id = bp.partnership_id
                JOIN batting_innings bi2 ON bi2.partnership_id = bp.partnership_id AND ABS(bi1.batting_position - bi2.batting_position) = 1
                JOIN players p1 ON p1.player_id = bi1.player_id
                JOIN players p2 ON p2.player_id = bi2.player_id AND p2.player_id > p1.player_id
                WHERE bp.runs >= 100
                GROUP BY bp.partnership_id
                ORDER BY bp.runs DESC;
            """,

            # Q14
            "Q14. Bowling at venues (>=3 matches, >=4 overs each match)": """
                /* Expected tables:
                   bowling_innings(innings_id, match_id, player_id, overs, runs_conceded, wickets, venue_id)
                   matches(match_id, venue_id)
                   venues(venue_id, venue_name)
                */
                WITH valid_spells AS (
                  SELECT bi.*, m.venue_id
                  FROM bowling_innings bi
                  JOIN matches m ON m.match_id = bi.match_id
                  WHERE bi.overs >= 4
                ),
                agg AS (
                  SELECT player_id, venue_id,
                         COUNT(DISTINCT match_id) AS matches_played,
                         SUM(runs_conceded) * 1.0 / NULLIF(SUM(overs),0) AS economy_rate,
                         SUM(wickets) AS total_wickets
                  FROM valid_spells
                  GROUP BY player_id, venue_id
                  HAVING COUNT(DISTINCT match_id) >= 3
                )
                SELECT p.name AS bowler, v.venue_name, a.matches_played,
                       ROUND(a.economy_rate,2) AS avg_economy,
                       a.total_wickets
                FROM agg a
                JOIN players p ON p.player_id = a.player_id
                JOIN venues v ON v.venue_id = a.venue_id
                ORDER BY v.venue_name, avg_economy ASC, total_wickets DESC;
            """,

            # Q15
            "Q15. Players in close matches (<50 runs OR <5 wickets)": """
                /* Expected tables:
                   matches(match_id, winner_team, victory_type, victory_margin, team1, team2)
                   batting_innings(match_id, player_id, runs, team)
                */
                WITH close_matches AS (
                  SELECT match_id, winner_team
                  FROM matches
                  WHERE (victory_type='runs' AND victory_margin < 50)
                     OR (victory_type='wickets' AND victory_margin < 5)
                ),
                per_player AS (
                  SELECT bi.player_id, bi.match_id, bi.runs, bi.team
                  FROM batting_innings bi
                  JOIN close_matches cm ON cm.match_id = bi.match_id
                )
                SELECT p.name AS player,
                       ROUND(AVG(per.runs),2) AS avg_runs_close,
                       COUNT(*) AS close_matches_played,
                       SUM(CASE WHEN cm.winner_team = per.team THEN 1 ELSE 0 END) AS team_wins_when_batted
                FROM per_player per
                JOIN close_matches cm ON cm.match_id = per.match_id
                JOIN players p ON p.player_id = per.player_id
                GROUP BY p.name
                HAVING close_matches_played >= 1
                ORDER BY avg_runs_close DESC;
            """,

            # Q16
            "Q16. Since 2020: yearly avg runs & strike rate (>=5 matches/year)": """
                /* Expected tables:
                   batting_innings(match_id, player_id, runs, balls_faced, match_date)
                */
                WITH bi AS (
                  SELECT player_id,
                         strftime('%Y', match_date) AS yr,
                         match_id,
                         runs,
                         balls_faced
                  FROM batting_innings
                  WHERE DATE(match_date) >= DATE('2020-01-01')
                ),
                per_year AS (
                  SELECT player_id, yr,
                         COUNT(DISTINCT match_id) AS matches_played,
                         AVG(runs*1.0) AS avg_runs,
                         AVG(CASE WHEN balls_faced>0 THEN (runs*100.0/balls_faced) ELSE NULL END) AS avg_sr
                  FROM bi
                  GROUP BY player_id, yr
                  HAVING COUNT(DISTINCT match_id) >= 5
                )
                SELECT p.name, yr, ROUND(avg_runs,2) AS avg_runs, ROUND(avg_sr,2) AS avg_strike_rate, matches_played
                FROM per_year
                JOIN players p ON p.player_id = per_year.player_id
                ORDER BY p.name, yr;
            """,

            # Q17
            "Q17. Does winning the toss help? Win% by toss decision": """
                /* Expected tables:
                   matches(match_id, toss_winner, toss_decision, winner_team)
                */
                WITH base AS (
                  SELECT toss_decision,
                         COUNT(*) AS total,
                         SUM(CASE WHEN toss_winner = winner_team THEN 1 ELSE 0 END) AS wins_when_toss_winner_wins
                  FROM matches
                  WHERE toss_winner IS NOT NULL AND toss_decision IN ('bat','bowl')
                  GROUP BY toss_decision
                )
                SELECT toss_decision,
                       total,
                       ROUND(wins_when_toss_winner_wins * 100.0 / total, 2) AS win_pct_for_toss_winner
                FROM base
                ORDER BY toss_decision;
            """,

            # Q18
            "Q18. Most economical bowlers (ODI & T20, min 10 matches, avg >=2 overs)": """
                /* Expected tables:
                   bowling_innings(match_id, player_id, format, overs, runs_conceded, wickets)
                */
                WITH lo AS (
                  SELECT player_id,
                         COUNT(DISTINCT match_id) AS matches_bowled,
                         SUM(overs) AS overs_total,
                         SUM(runs_conceded) AS runs_total,
                         SUM(wickets) AS wickets_total
                  FROM bowling_innings
                  WHERE format IN ('ODI','T20I')
                  GROUP BY player_id
                )
                SELECT p.name AS bowler,
                       ROUND(runs_total * 1.0 / NULLIF(overs_total,0), 2) AS economy_rate,
                       wickets_total,
                       matches_bowled
                FROM lo
                JOIN players p ON p.player_id = lo.player_id
                WHERE matches_bowled >= 10
                  AND (overs_total * 1.0 / matches_bowled) >= 2.0
                ORDER BY economy_rate ASC, wickets_total DESC;
            """,

            # Q19
            "Q19. Consistency: avg runs & stdev (since 2022, >=10 balls/inn)": """
                /* SQLite lacks STDDEV by default. We'll approximate via variance formula.
                   Expected tables: batting_innings(player_id, runs, balls_faced, match_date)
                */
                WITH filt AS (
                  SELECT player_id, runs*1.0 AS runs
                  FROM batting_innings
                  WHERE DATE(match_date) >= DATE('2022-01-01')
                    AND balls_faced >= 10
                ),
                agg AS (
                  SELECT player_id,
                         COUNT(*) AS n,
                         AVG(runs) AS avg_runs,
                         AVG(runs * runs) AS avg_runs_sq
                  FROM filt
                  GROUP BY player_id
                )
                SELECT p.name,
                       ROUND(agg.avg_runs,2) AS avg_runs,
                       ROUND(CASE
                         WHEN n > 1 THEN sqrt(agg.avg_runs_sq - (agg.avg_runs * agg.avg_runs))
                         ELSE NULL
                       END, 2) AS stdev_runs,
                       n AS innings_count
                FROM agg
                JOIN players p ON p.player_id = agg.player_id
                WHERE innings_count >= 1
                ORDER BY stdev_runs ASC NULLS LAST, avg_runs DESC;
            """,

            # Q20
            "Q20. Matches & batting average by format (players with >=20 total matches)": """
                /* Expected tables:
                   batting_totals(player_id, format, matches, runs_total, outs)
                */
                WITH per_format AS (
                  SELECT player_id, format, matches,
                         CAST(runs_total AS FLOAT)/NULLIF(outs,0) AS batting_avg
                  FROM batting_totals
                ),
                pivot AS (
                  SELECT player_id,
                         SUM(CASE WHEN format='Test' THEN matches ELSE 0 END) AS test_matches,
                         SUM(CASE WHEN format='ODI'  THEN matches ELSE 0 END) AS odi_matches,
                         SUM(CASE WHEN format='T20I' THEN matches ELSE 0 END) AS t20i_matches,
                         AVG(CASE WHEN format='Test' THEN batting_avg END) AS test_avg,
                         AVG(CASE WHEN format='ODI'  THEN batting_avg END) AS odi_avg,
                         AVG(CASE WHEN format='T20I' THEN batting_avg END) AS t20i_avg,
                         SUM(matches) AS total_matches
                  FROM per_format
                  GROUP BY player_id
                )
                SELECT p.name,
                       test_matches, ROUND(test_avg,2) AS test_avg,
                       odi_matches,  ROUND(odi_avg,2)  AS odi_avg,
                       t20i_matches, ROUND(t20i_avg,2) AS t20i_avg,
                       total_matches
                FROM pivot
                JOIN players p ON p.player_id = pivot.player_id
                WHERE total_matches >= 20
                ORDER BY total_matches DESC;
            """,

            # Q21
            "Q21. Composite performance score & ranking by format": """
                /* Expected tables:
                   player_format_summary(player_id, format, runs_scored, batting_average, strike_rate,
                                         wickets_taken, bowling_average, economy_rate, catches, stumpings)
                */
                WITH scored AS (
                  SELECT player_id, format,
                    ((runs_scored * 0.01) + (batting_average * 0.5) + (strike_rate * 0.3)) AS batting_points,
                    ((wickets_taken * 2.0) + ((50 - bowling_average) * 0.5) + ((6 - economy_rate) * 2.0)) AS bowling_points,
                    (catches * 0.5 + stumpings * 1.0) AS fielding_points
                  FROM player_format_summary
                ),
                total AS (
                  SELECT player_id, format,
                         batting_points + bowling_points + fielding_points AS total_points
                  FROM scored
                )
                SELECT p.name, format,
                       ROUND(total_points,2) AS total_points
                FROM total
                JOIN players p ON p.player_id = total.player_id
                ORDER BY format, total_points DESC;
            """,

            # Q22
            "Q22. Head-to-head analysis (last 3 years, pairs with >=5 matches)": """
                /* Expected tables:
                   matches(match_id, match_date, team1, team2, winner_team, victory_type, victory_margin, toss_decision, venue_id, batting_first_team)
                   venues(venue_id, venue_name)
                */
                WITH recent AS (
                  SELECT * FROM matches
                  WHERE DATE(match_date) >= DATE('now', '-3 years')
                ),
                normalized AS (
                  SELECT CASE WHEN team1 < team2 THEN team1 ELSE team2 END AS team_a,
                         CASE WHEN team1 < team2 THEN team2 ELSE team1 END AS team_b,
                         *
                  FROM recent
                ),
                base AS (
                  SELECT team_a, team_b,
                         COUNT(*) AS total_matches,
                         SUM(CASE WHEN winner_team = team_a THEN 1 ELSE 0 END) AS wins_a,
                         SUM(CASE WHEN winner_team = team_b THEN 1 ELSE 0 END) AS wins_b,
                         AVG(CASE WHEN winner_team = team_a THEN victory_margin END) AS avg_margin_a,
                         AVG(CASE WHEN winner_team = team_b THEN victory_margin END) AS avg_margin_b,
                         SUM(CASE WHEN batting_first_team = team_a THEN 1 ELSE 0 END) AS a_bat_first_cnt,
                         SUM(CASE WHEN batting_first_team = team_b THEN 1 ELSE 0 END) AS b_bat_first_cnt
                  FROM normalized
                  GROUP BY team_a, team_b
                  HAVING COUNT(*) >= 5
                )
                SELECT team_a, team_b,
                       total_matches,
                       wins_a, wins_b,
                       ROUND(wins_a * 100.0 / total_matches,2) AS win_pct_a,
                       ROUND(wins_b * 100.0 / total_matches,2) AS win_pct_b,
                       ROUND(avg_margin_a,2) AS avg_victory_margin_when_a_wins,
                       ROUND(avg_margin_b,2) AS avg_victory_margin_when_b_wins
                FROM base
                ORDER BY total_matches DESC, ABS(win_pct_a - win_pct_b) DESC;
            """,

            # Q23
            "Q23. Recent form (last 10 innings): avgs, SR trend, 50+ counts, consistency": """
                /* Expected tables:
                   batting_innings(player_id, match_date, runs, balls_faced)
                */
                WITH last10 AS (
                  SELECT player_id, match_date, runs, balls_faced,
                         ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY DATE(match_date) DESC) AS rn
                  FROM batting_innings
                ),
                scoped AS (
                  SELECT * FROM last10 WHERE rn <= 10
                ),
                last5 AS (
                  SELECT player_id, AVG(runs*1.0) AS avg_last5
                  FROM scoped WHERE rn <= 5 GROUP BY player_id
                ),
                last10agg AS (
                  SELECT player_id,
                         AVG(runs*1.0) AS avg_last10,
                         AVG(CASE WHEN balls_faced>0 THEN (runs*100.0/balls_faced) END) AS avg_sr_last10,
                         SUM(CASE WHEN runs >= 50 THEN 1 ELSE 0 END) AS fifties_last10,
                         COUNT(*) AS n,
                         AVG(runs*1.0) AS mean_r,
                         AVG((runs*1.0)*(runs*1.0)) AS mean_r2
                  FROM scoped
                  GROUP BY player_id
                ),
                merged AS (
                  SELECT l10.player_id,
                         l5.avg_last5,
                         l10.avg_last10,
                         l10.avg_sr_last10,
                         l10.fifties_last10,
                         l10.n,
                         sqrt(l10.mean_r2 - (l10.mean_r*l10.mean_r)) AS stdev_r
                  FROM last10agg l10
                  LEFT JOIN last5 l5 ON l5.player_id = l10.player_id
                )
                SELECT p.name,
                       ROUND(avg_last5,2) AS avg_last5,
                       ROUND(avg_last10,2) AS avg_last10,
                       ROUND(avg_sr_last10,2) AS sr_last10,
                       fifties_last10,
                       ROUND(stdev_r,2) AS consistency_stdev,
                       CASE
                         WHEN avg_last5 >= 50 AND stdev_r <= 15 THEN 'Excellent Form'
                         WHEN avg_last5 >= 35 THEN 'Good Form'
                         WHEN avg_last5 >= 20 THEN 'Average Form'
                         ELSE 'Poor Form'
                       END AS form_bucket
                FROM merged
                JOIN players p ON p.player_id = merged.player_id
                ORDER BY form_bucket, avg_last5 DESC;
            """,

            # Q24
            "Q24. Best batting partnerships (adjacent, >=5 partnerships)": """
                /* Expected tables:
                   partnerships(partnership_id, innings_id, runs)
                   partnership_players(partnership_id, player_id, batting_position)
                   players(player_id, name)
                */
                WITH pairs AS (
                  SELECT pp1.player_id AS p1,
                         pp2.player_id AS p2,
                         pr.runs
                  FROM partnership_players pp1
                  JOIN partnership_players pp2
                    ON pp1.partnership_id = pp2.partnership_id
                   AND ABS(pp1.batting_position - pp2.batting_position) = 1
                   AND pp1.player_id < pp2.player_id
                  JOIN partnerships pr ON pr.partnership_id = pp1.partnership_id
                ),
                stats AS (
                  SELECT p1, p2,
                         COUNT(*) AS partnerships_played,
                         AVG(runs*1.0) AS avg_runs,
                         SUM(CASE WHEN runs >= 50 THEN 1 ELSE 0 END) AS partnerships_50_plus,
                         MAX(runs) AS highest
                  FROM pairs
                  GROUP BY p1, p2
                  HAVING COUNT(*) >= 5
                )
                SELECT pA.name AS player_a, pB.name AS player_b,
                       ROUND(avg_runs,2) AS avg_partnership,
                       partnerships_50_plus,
                       highest,
                       ROUND(partnerships_50_plus * 100.0 / partnerships_played,2) AS success_rate_pct
                FROM stats
                JOIN players pA ON pA.player_id = stats.p1
                JOIN players pB ON pB.player_id = stats.p2
                ORDER BY success_rate_pct DESC, avg_partnership DESC, highest DESC;
            """,

            # Q25
            "Q25. Time-series: quarterly batting trend & career phase (>=6 quarters)": """
                /* Expected tables:
                   batting_innings(player_id, match_date, runs, balls_faced, match_id)
                */
                WITH base AS (
                  SELECT player_id,
                         strftime('%Y', match_date) AS y,
                         ((CAST(strftime('%m', match_date) AS INT) - 1) / 3) + 1 AS q,
                         match_id, runs, balls_faced
                  FROM batting_innings
                ),
                per_q AS (
                  SELECT player_id, y || 'Q' || q AS yrq,
                         COUNT(DISTINCT match_id) AS matches_q,
                         AVG(runs*1.0) AS avg_runs_q,
                         AVG(CASE WHEN balls_faced>0 THEN (runs*100.0/balls_faced) END) AS avg_sr_q
                  FROM base
                  GROUP BY player_id, yrq
                  HAVING COUNT(DISTINCT match_id) >= 3
                ),
                ranked AS (
                  SELECT *,
                         ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY yrq) AS rn
                  FROM per_q
                ),
                delta AS (
                  SELECT p1.player_id, p1.yrq,
                         p1.avg_runs_q,
                         p1.avg_sr_q,
                         (p1.avg_runs_q - p0.avg_runs_q) AS d_runs,
                         (p1.avg_sr_q - p0.avg_sr_q) AS d_sr
                  FROM ranked p1
                  LEFT JOIN ranked p0
                    ON p0.player_id = p1.player_id AND p0.rn = p1.rn - 1
                ),
                coverage AS (
                  SELECT player_id, COUNT(*) AS qtrs FROM per_q GROUP BY player_id
                )
                SELECT p.name,
                       yrq,
                       ROUND(avg_runs_q,2) AS avg_runs,
                       ROUND(avg_sr_q,2) AS avg_sr,
                       ROUND(d_runs,2) AS delta_runs_vs_prev_qtr,
                       ROUND(d_sr,2) AS delta_sr_vs_prev_qtr,
                       CASE
                         WHEN d_runs IS NULL THEN '—'
                         WHEN d_runs > 0 AND d_sr > 0 THEN 'Improving'
                         WHEN d_runs < 0 AND d_sr < 0 THEN 'Declining'
                         ELSE 'Stable'
                       END AS trend_this_qtr,
                       CASE
                         WHEN c.qtrs >= 6 THEN
                           CASE
                             WHEN AVG(CASE WHEN d_runs > 0 AND d_sr > 0 THEN 1 ELSE 0 END) OVER (PARTITION BY d.player_id) >= 0.6
                               THEN 'Career Ascending'
                             WHEN AVG(CASE WHEN d_runs < 0 AND d_sr < 0 THEN 1 ELSE 0 END) OVER (PARTITION BY d.player_id) >= 0.6
                               THEN 'Career Declining'
                             ELSE 'Career Stable'
                           END
                         ELSE 'Insufficient span'
                       END AS career_phase_estimate
                FROM delta d
                JOIN players p ON p.player_id = d.player_id
                JOIN coverage c ON c.player_id = d.player_id
                ORDER BY p.name, yrq;
            """,
        }

        choice = st.selectbox("📌 Select Query", list(queries.keys()))
        query = queries[choice]

        st.code(sqlparse.format(query, reindent=True, keyword_case="upper"), language="sql")

        if st.button("Run Predefined Query"):
            try:
                df = run_query(query)
                if df.empty:
                    st.warning("⚠️ No results found for this query.")
                else:
                    st.dataframe(df)
            except Exception as e:
                st.error(f"❌ Error while running this query. You may need to tweak table/column names.\n\n{e}")

    # ---------------------- Custom Query Section ----------------------
    with tab2:
        st.header("💡 Custom SQL Playground")

        # Move the table explorer into the main tab (not sidebar)
        st.subheader("📂 Table Explorer")
        tables = get_tables()
        selected_tables = st.multiselect("Select Tables (for joins)", tables)

        # Show schemas in collapsible expanders on main page
        if selected_tables:
            st.subheader("📑 Selected Table Schemas")
            for table in selected_tables:
                with st.expander(f"Schema: {table}", expanded=False):
                    schema = get_table_schema(table)
                    st.dataframe(schema[["cid", "name", "type"]])

        # Default query suggestion
        if selected_tables:
            if len(selected_tables) == 1:
                default_query = f"SELECT * FROM {selected_tables[0]} LIMIT 10;"
            else:
                default_query = f"""
                SELECT *
                FROM {selected_tables[0]} a
                JOIN {selected_tables[1]} b
                  ON a.id = b.id
                LIMIT 10;
                """
        else:
            default_query = "SELECT name FROM sqlite_master WHERE type='table';"

        user_query = st.text_area("✍️ Write your SQL query here:", default_query.strip(), height=150)

        st.code(sqlparse.format(user_query, reindent=True, keyword_case="upper"), language="sql")

        if st.button("Run Custom Query"):
            try:
                df = run_query(user_query)
                if df.empty:
                    st.warning("⚠️ No results found for this query.")
                else:
                    st.dataframe(df)
            except Exception as e:
                st.error(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
