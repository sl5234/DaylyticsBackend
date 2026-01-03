"""
Temporary hardcoded prompt for metric generation.

This file contains prompts that will be used by StartWorkflow
until the proper prompt system is implemented.
"""

PERSONAL_PROMPT_TEMPORARY = [
"""
Calculate total time spent on workout activities for the day.

Title: TotalWorkoutTimePerDay

Steps:
1. Iterate through each activity log. Filter activity logs with tag "workout". Create a list of such logs.
2. Iterate through each activity log. Filter activity logs with tag "cardio". Create a list of such logs.
3. Merge all lists.
4. Iterate through each log in the merged list. Sum durations of all logs.

Rules:
1. If there are no activity logs with tag "workout", "cardio", return 0 as the total time spent on workout activities for the day.
""",

"""
Calculate total time spent on family activities for the day.

Title: TotalFamilyTimePerDay

Steps:
1. Iterate through each activity log. Filter activity logs with tag "family". Create a list of such logs.
2. Iterate through each activity log. Filter activity logs with tag "parent". Create a list of such logs.
3. Iterate through each activity log. Filter activity logs with tag "dad". Create a list of such logs.
4. Iterate through each activity log. Filter activity logs with tag "mom". Create a list of such logs.
5. Iterate through each activity log. Filter activity logs with tag "brother". Create a list of such logs.
6. Merge all lists.
7. Iterate through each log in the merged list. Sum durations of all logs.

Rules:
1. If there are no activity logs with tag "family", "parent", "dad", "mom", or "brother", return 0 as the total time spent on family activities for the day.
""",

"""
Calculate total time spent on research activities for the day.

Title: TotalResearchTimePerDay

Steps:
1. Iterate through each activity log. Filter activity logs with tag "research". Create a list of such logs.
2. Iterate through each log in the list. Sum durations of all logs.

Rules:
1. If there are no activity logs with tag "research", return 0 as the total time spent on research activities for the day.
""",

"""
Calculate total time spent on reading activities for the day.

Title: TotalReadingTimePerDay

Steps:
1. Iterate through each activity log. Filter activity logs with tag "daily_reading". Create a list of such logs.
2. Iterate through each log in the list. Sum durations of all logs.

Rules:
1. If there are no activity logs with tag "daily_reading", return 0 as the total time spent on reading activities for the day.
""",

"""
Calculate total time spent on Amazon activities for the day.

Title: TotalAmazonTimePerDay

Steps:
1. Iterate through each activity log. Filter activity logs with tag "work". Create a list of such logs.
2. Iterate through each log in the list. Sum durations of all logs.

Rules:
1. If there are no activity logs with tag "work", return 0 as the total time spent on Amazon activities for the day.
""",

"""
Calculate total time spent on app building activities for the day.

Title: TotalAppBuildingTimePerDay

Steps:
1. Iterate through each activity log. Filter activity logs with tag "application_building". Create a list of such logs.
2. Iterate through each log in the list. Sum durations of all logs.

Rules:
1. If there are no activity logs with tag "application_building", return 0 as the total time spent on app building activities for the day.
""",

"""
Calculate total time spent on finance activities for the day.

Title: TotalFinanceTimePerDay

Steps:
1. Iterate through each activity log. Filter activity logs with tag "finance". Create a list of such logs.
2. Iterate through each activity log. Filter activity logs with tag "daily_accounting". Create a list of such logs.
3. Iterate through each activity log. Filter activity logs with tag "weekly_accounting". Create a list of such logs.
4. Merge all lists.
5. Iterate through each log in the merged list. Sum durations of all logs.

Rules:
1. If there are no activity logs with tag "finance", "daily_accounting", "weekly_accounting", return 0 as the total time spent on finance activities for the day.
""",

"""
Calculate total time spent on language study activities for the day.

Title: TotalLanguageStudyTimePerDay

Steps:
1. Iterate through each activity log. Filter activity logs with tag "language_study". Create a list of such logs.
2. Iterate through each log in the list. Sum durations of all logs.

Rules:
1. If there are no activity logs with tag "language_study", return 0 as the total time spent on language study activities for the day.
""",

"""
Calculate total time spent on dating activities for the day.

Title: TotalDatingTimePerDay

Steps:
1. Iterate through each activity log. Filter activity logs with tag "zexin". Create a list of such logs.
2. Iterate through each log in the list. Sum durations of all logs.

Rules:
1. If there are no activity logs with tag "zexin", return 0 as the total time spent on dating activities for the day.
""",

"""
Wake up time for the day.

Title: WakeUpTimePerDay

Steps:
1. Iterate through each activity log. Filter activity logs with tag "bed_time". Create a list of such logs.
2. Iterate through each log in the list. Extract the log with earliest start time.
3. Get end time of that log.
4. Calculate minutes passed between 00:00:00 and end time.

Rules:
1. If there are no activity logs with tag "bed_time", do not return any value.
""",

"""
Bed time for the day.

Title: BedTimePerDay

Steps:
1. Iterate through each activity log. Filter activity logs with tag "bed_time". Create a list of such logs.
2. Iterate through each log in the list. Extract the log with latest start time.
3. Get start time of that log.
4. Calculate minutes passed between 00:00:00 and start time.

Rules:
1. If there are no activity logs with tag "bed_time", do not return any value.
""",

"""
Total unrecorded time for the day.

Title: UnrecordedTimePerDay

Steps:
1. Sort all activity logs by start time.
2. Iterate through each activity log. Extract intervals [start time, end time] for each log.
3. Create a list of all intervals starting with 00:00:00 and ending with 23:59:59. For example, [00:00:00, start time, end time, start time 2, end time 2, ..., 23:59:59].
4. Create an empty list for gap durations.
5. Iterate through each element in the list of intervals. If first element, continue. Else, calculate minutes passed between the previous element and the current element. This is the gap duration. Append this gap duration to the list of gap durations.
6. Sum all elements in the list of gap durations. This is the total unrecorded time for the day.

Rules:
1. If there are no activity logs, return 1440 minutes as the total unrecorded time for the day.
2. Do NOT compute this as (24h - sum of activity durations).
3. Note that there will not be any activity logs that overlap with each other.
4. At the end, return the total unrecorded time for the day in minutes in a single metric object.
""",

"""
Calculate total time spent on work activities for the day.

Title: TotalWorkTimePerDay

Steps:
1. Iterate through each activity log. Filter activity logs with tag "research". Create a list of such logs.
1. Iterate through each activity log. Filter activity logs with tag "daily_reading". Create a list of such logs.
1. Iterate through each activity log. Filter activity logs with tag "work". Create a list of such logs.
1. Iterate through each activity log. Filter activity logs with tag "application_building". Create a list of such logs.
2. Iterate through each activity log. Filter activity logs with tag "finance". Create a list of such logs.
2. Iterate through each activity log. Filter activity logs with tag "daily_accounting". Create a list of such logs.
3. Iterate through each activity log. Filter activity logs with tag "weekly_accounting". Create a list of such logs.
1. Iterate through each activity log. Filter activity logs with tag "language_study". Create a list of such logs.
4. Merge all lists.
5. Iterate through each log in the merged list. Sum durations of all logs.

Rules:
1. If there are no activity logs with aformentioned tags, return 0 as the total time spent on work activities for the day.
""",
]

