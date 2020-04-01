import imagehash
import time
import os
import shutil
from PIL import Image


# Clears the Progress folder
folder = 'Progress/'
for filename in os.listdir(folder):
    file_path = os.path.join(folder, filename)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    except Exception as e:
        print('Failed to delete %s. Reason: %s' % (file_path, e))


# Replace a specific index of a string
def index_replace(string, newstring, index):
    return string[:index] + newstring + string[index+1:]


# Reads the image and writes it to an array, set as a function for cleanliness
def read_img(path):
    # Defines cell height and width of puzzle
    global img, pwidth, pheight, hash_cutoff, readerrors, readerror
    img = Image.open(path)
    pwidth = int((img.size[0] - 1) / 23)
    pheight = int((img.size[1] - 1) / 23)
    print("Height:", pheight, "Width:", pwidth)

    print(img.size)

    # Creates an empty array with an amount of rows equal to puzzle height
    array = []
    for r in range(pheight):
        array.append('')

    # Goes across each cell and writes it into an array
    box = (0, 0, 24, 24)
    boxpos = (0, 0)
    emptyhash = imagehash.average_hash(Image.open('emptySquare.jpg'))
    blackhash = imagehash.average_hash(Image.open('blacksquare.jpg'))
    whitehash = imagehash.average_hash(Image.open('whitesquare.jpg'))
    hash_cutoff = 1

    readerrors = 0
    readerror = True
    while readerror:
        readerror = False
        while box[3] <= img.size[1]:
            while box[2] <= img.size[0]:
                sourcehash = imagehash.average_hash(img.crop(box))
                for i in [(emptyhash, 'x'), (blackhash, '1'), (whitehash, '0')]:
                    if sourcehash - i[0] < hash_cutoff:
                        array[boxpos[1]] = array[boxpos[1]] + i[1]
                box = (box[0] + 23, box[1], box[2] + 23, box[3])
                boxpos = (boxpos[0] + 1, boxpos[1])
            else:
                box = (0, box[1] + 23, 24, box[3] + 23)
                boxpos = (0, boxpos[1] + 1)

        readerrorcheck(array)

        if hash_cutoff > 30:
            print("Cannot read image, stopping")
            input()
            quit()

    if not readerrorcheck(array):
        write_img(array, "Progress/HCF")
        print("Something went wrong while attempting to read the image. Check HCF.jpg for error location")
        input()
        quit()

    return array


# Writes the solution to a new image
def write_img(array, imgname):
    emptyimg = Image.open('emptySquare.jpg')
    blackimg = Image.open('blacksquare.jpg')
    whiteimg = Image.open('whitesquare.jpg')
    emptycopy = emptyimg.copy()
    blackcopy = blackimg.copy()
    whitecopy = whiteimg.copy()
    output = Image.new('RGB', img.size, color='red')
    currpos = (0, 0)
    for r in array:
        for character in r:
            for x in [(emptycopy, 'x'), (blackcopy, '1'), (whitecopy, '0')]:
                if character == x[1]:
                    output.paste(x[0], currpos)
            currpos = (currpos[0] + 23, currpos[1])
        currpos = (0, currpos[1] + 23)

    output.save(imgname + '.jpg')


# Checks for unread cells of the puzzle in read_img. I didn't add this to that function because I'm lazy and fuck you
def readerrorcheck(array):
    global readerror, readerrors, hash_cutoff
    for r in array:
        if len(r) != pwidth:
            write_img(array, 'Progress/Readerror' + str(readerrors))
            readerror = True
            readerrors += 1
            hash_cutoff += 1
            return False
    return True


# Solves obvious moves, should be used as often as possible
def simplemoves(line):
    move = {"AAB": "AAx", "BAA": "xAA", "ABA": "AxA"}

    for b in [("0", "1"), ("1", "0")]:
        for m in move:
            line = line.replace(move[m].replace("A", b[0]).replace("B", b[1]), m.replace("A", b[0]).replace("B", b[1]))

        if line.count(b[0]) == len(line) / 2:
            line = line.replace("x", b[1])

    return line


# Solves lines by process of elimination
# This function takes a lot of time to run on bigger puzzles, so it breaks the moment it makes a single change in order
# to let simplemoves do the bulk of the work
def complexmoves(array):
    global changecount
    result = array.copy()
    updated = False

    for r in range(len(result)):
        if result[r].count('x') == 0:
            continue

        xindex = [c for c in range(len(result[r])) if result[r][c] == "x"]  # Indexes every occurance of x in the row
        solutions = []
        maxone = (len(result[r])/2) - result[r].count('1')
        maxzero = (len(result[r])/2) - result[r].count('0')
        if 2**len(xindex) > 100000:  # Sanity check to make sure it's not stuck in an infinite loop somewhere
            spaces = ''
            for space in range(15 - len(str(2**len(xindex)))):
                spaces = spaces + ' '
            print("Checking a big number... Range:", 2**len(xindex), end=spaces)

        for n in range((2**len(xindex))):
            n = str(bin(n)[2:].zfill(len(xindex)))  # Converts n to binary
            if n.count('1') > maxone or n.count('0') > maxzero:
                continue
            test = result[r]
            for index in range(len(xindex)):  # Replaces every indexed X with the appropriate n
                test = test[:xindex[index]] + n[index] + test[xindex[index]+1:]
            if test.count("000") == 0 and test.count("111") == 0 and test.count("1") == test.count("0") and\
                    test not in result:
                # Checks if this config of test is valid and saves it
                solutions.append(n)

        if 2**len(xindex) > 100000:
            print("Done!")

        if len(solutions) == 1:  # If there's only one solution then that must be it
            for c in range(len(solutions[0])):
                result[r] = index_replace(result[r], solutions[0][c], xindex[c])

        elif len(solutions) > 1:
            # Checks c position of every solution
            # If they're all the same, that piece is placed at the index position
            for c in range(len(solutions[0])):
                consistent = True
                for s in range(len(solutions)):
                    if solutions[s][c] != solutions[0][c]:
                        consistent = False

                if consistent:
                    result[r] = index_replace(result[r], solutions[0][c], xindex[c])
                    updated = True
                if updated:
                    break

    # Validity check
    prev_rotated_result = result
    for rotation in range(4):
        new_rotated_result = list(map(''.join, list(zip(*prev_rotated_result[::-1]))))
        for r in new_rotated_result:
            if r.count("111") > 0 or r.count("000") > 0 or r.count("1") > len(r) / 2 or r.count("0") > len(r) / 2:
                return array
        prev_rotated_result = new_rotated_result.copy()

    return result


# Rotates the puzzle, does moves. If any moves occurred, repeats the process
def moveloop(array):
    global changecount
    p_rot_array = array.copy()
    n_rot_array = []
    changed = True
    while changed:
        changed = False
    
        # Rotating the puzzle
        for turn in range(4):
            n_rot_array = list(map(''.join, list(zip(*p_rot_array[::-1]))))
    
            array_before = n_rot_array.copy()
            n_rot_array = list(map(simplemoves, n_rot_array))

            if array_before != n_rot_array:
                changed = True
    
            p_rot_array = n_rot_array.copy()
    
            for r in n_rot_array:
                if r.count("111") > 0 or r.count("000") > 0 or r.count("1") > len(r)/2 or r.count("0") > len(r)/2 or\
                        len(n_rot_array) != len(set(n_rot_array)):
                    return None
    
        if changed:
            array = n_rot_array.copy()
            changecount += 1
            print("Finished pass", changecount)
            write_img(array, "Progress/Pass" + str(changecount))
        else:
            for turn in range(4):
                n_rot_array = list(map(''.join, list(zip(*p_rot_array[::-1]))))
                array_before = n_rot_array.copy()
                n_rot_array = complexmoves(n_rot_array)
                if array_before != n_rot_array:
                    changed = True
                    changecount += 1
                p_rot_array = n_rot_array.copy()
    
                for r in n_rot_array:
                    if r.count("111") > 0 or r.count("000") > 0\
                            or r.count("1") > len(r)/2 or r.count("0") > len(r)/2 or\
                            len(n_rot_array) != len(set(n_rot_array)):
                        return None
    
                if changed:  # If a single change has been made, reset the puzzle and try simple moves again
                    for t in range(3-turn):
                        n_rot_array = list(map(''.join, list(zip(*p_rot_array[::-1]))))
    
            if changed:
                array = n_rot_array.copy()
                changecount += 1
                print("Finished pass", changecount)
                write_img(array, "Progress/Pass" + str(changecount))
    return array


# Checks if the puzzle has been solved
def checksolved(array):
    for r in array:
        if r.count('x') > 0:
            return False
    return True


# Guesses the first empty piece of the puzzle
def guess(array):
    for r in range(len(array)):
        for char in range(len(array[r])):
            if array[r][char] == "x":
                for tup in ('0', '1'):
                    array[r] = index_replace(array[r], tup, char)
                    savedarray = array.copy()
                    array = moveloop(array)
                    if array is None:
                        array = savedarray.copy()
                        array[r] = index_replace(array[r], "x", char)
                    elif not checksolved(array):
                        array = guess(array)
                        if array is None:
                            array = savedarray.copy()

                    if array is not None and checksolved(array):
                        return array
    return array


# Prints the puzzle array for my own sanity
puzzleArray = read_img("puzzle.jpg")
empty = 0
print("Puzzle:")
for row in puzzleArray:
    print(row)
    empty = empty + ((len(row)/2) - row.count("1")) + ((len(row)/2) - row.count("0"))
print("Empty:", int(empty), '\n\n')


start = time.time()
changecount = 0
puzzleSave = puzzleArray.copy()  # If something goes wrong, moveloop returns None, this is an emergency backup
puzzleArray = moveloop(puzzleArray)
# If the puzzle hasn't been solved, makes a guess and tries again
if puzzleArray is None:
    puzzleArray = guess(puzzleSave)
if not checksolved(puzzleArray):
    puzzleArray = guess(puzzleArray)


# Stops the clock and writes the solution to an image
end = round(time.time()-start, 3)
write_img(puzzleArray, "Solution")


# Prints the solved array for my own sanity
if checksolved(puzzleArray):
    print("\n\nSolution:")
else:
    print("\n\nCould not complete puzzle. Perhaps you made a wrong move before showing it to me?\n\nProgress:")
solved = 0
for row in puzzleArray:
    print(row)
    solved = solved + ((len(row)/2) - row.count("1")) + ((len(row)/2) - row.count("0"))
solved = int(empty - solved)
print("Solved: " + str(solved) + "  Passes: " + str(changecount))
print(str(int((solved/empty)*100)) + "% Completed")
print("Time Elapsed: ", end, "seconds")
input()
