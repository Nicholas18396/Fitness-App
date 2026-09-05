def greet(s):
    print("Hey " + s)

greet("alvin")
greet("jason")
greet("how now brown cow")

def maxValue(arr):
    maxx = -9999999999999999999999
    for i in range(len(arr)):
        if arr[i] > maxx:
            maxx = arr[i]
    print(maxx)

maxValue([4, 7, 2, 8, 10, 9])
maxValue([10, 5, 40, 40.3])
maxValue([-5, -2, -1, -11])
maxValue([42])
maxValue([1000, 8])
maxValue([1000, 8, 9000])
maxValue([2, 5, 1, 1, 4])

def longestWord(sentence):
    longest = ""
    current_length = ""

    for i in range(len(sentence)):
        if sentence[i] != " ":
            current_length += sentence[i]
        else:
            current_length = ""
        if len(current_length) > len(longest):
            longest = current_length
    print(longest)
longestWord("hello there friend")
longestWord("what a wonderful world")
longestWord("who did eat the ham")
longestWord("the quick brown fox jumped over the log")
longestWord("potato")