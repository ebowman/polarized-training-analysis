#!/usr/bin/env python3
import json
from collections import Counter

# Load recent activities and check for duplicates
with open('recent_activities.json', 'r') as f:
    activities = json.load(f)

print(f'Total activities: {len(activities)}')

# Check for duplicate IDs
ids = [a['id'] for a in activities]
unique_ids = set(ids)
print(f'Unique activity IDs: {len(unique_ids)}')

if len(ids) != len(unique_ids):
    print('🚨 DUPLICATES FOUND!')
    duplicates = [id for id, count in Counter(ids).items() if count > 1]
    print(f'Duplicate IDs: {duplicates}')
    
    # Show duplicate activities
    for dup_id in duplicates:
        matches = [a for a in activities if a['id'] == dup_id]
        print(f'\nActivity ID {dup_id}:')
        for i, match in enumerate(matches):
            streams_count = len(match.get('streams', {})) if match.get('streams') else 0
            print(f'  Copy {i+1}: {match["name"]} - {streams_count} streams')
            
    # Remove duplicates - keep the one with more streams data
    unique_activities = []
    seen_ids = set()
    
    for activity in activities:
        if activity['id'] not in seen_ids:
            unique_activities.append(activity)
            seen_ids.add(activity['id'])
        else:
            # Check if this copy has more streams than the existing one
            existing_activity = next(a for a in unique_activities if a['id'] == activity['id'])
            existing_streams = len(existing_activity.get('streams', {}))
            current_streams = len(activity.get('streams', {}))
            
            if current_streams > existing_streams:
                # Replace with the better copy
                idx = next(i for i, a in enumerate(unique_activities) if a['id'] == activity['id'])
                unique_activities[idx] = activity
                print(f'Replaced activity {activity["id"]} with better copy ({current_streams} vs {existing_streams} streams)')
    
    print(f'\nCleaned activities: {len(unique_activities)}')
    
    # Save cleaned data
    with open('recent_activities.json', 'w') as f:
        json.dump(unique_activities, f, indent=2)
    
    print('✅ Duplicates removed and saved!')
else:
    print('✅ No duplicates found!')