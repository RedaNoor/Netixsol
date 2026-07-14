
def calculate_mean(numbers):
    total = 0

    for num in numbers:
        total=total+num
    return total/len(numbers)
    
def calculate_median(numbers):
    sorted_numbers = sorted(numbers)
    n= len(sorted_numbers)

    if n % 2 == 1:
        return sorted_numbers[n//2]
    else:
        m1=sorted_numbers[(n//2) - 1]
        m2=sorted_numbers[n//2]
        return (m1+m2)/2
def calculate_mode(numbers):
    freq={}

    for num in numbers:
        if num in freq:
            freq[num]+=1
        else:
            freq[num]=1
    max_count=max(freq.values())

    modes=[]

    for key, value in freq.items():
        if value==max_count:
            modes.append(key)
    return modes

def calculate_min(numbers):
    minimum=numbers[0]

    for num in numbers:
        if num<minimum:
            minimum=num
    return minimum

def calculate_max(numbers):
    maximum=numbers[0]

    for num in numbers:
        if num>maximum:
            maximum=num
    return maximum

#Main
user_input=input("Enter the numbers separated by spaces: ")

numbers = []

for item in user_input.split():
    numbers.append(float(item))
print("\nResults")
print("Mean   :", calculate_mean(numbers))
print("Median :", calculate_median(numbers))
print("Mode   :", calculate_mode(numbers))
print("Min    :", calculate_min(numbers))
print("Max    :", calculate_max(numbers))
