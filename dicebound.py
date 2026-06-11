"""
=============================================================
  DICEBOUND - A Luck-Dice Based Rougelike Game
=============================================================
"""

"""
How to play:
  1. Run this file with Python: dicebound.py
  2. Choose New Game or Load Game from the main menu.
  3. Each turn, you roll 5 dice. You can reroll up to 3 times.
  4. After rolling, your dice are scored as a combination, 
     and you deal damage to the enemy.
  5. Special upgrades on each die slot (Poison, Crit, Heal)
     activate when that die is part of your winning combo.
  6. Defeat enemies to earn gold, then buy upgrades in the shop.
  7. Every 5th level is a Mini Boss; every 10th is a Boss.
  8. The game goes on forever -- how far can you reach?
"""

from os import remove
from random import randrange
from os.path import exists

# --------------------------------------------------
# Starting Constants
# --------------------------------------------------

SAVE_FILE = __file__.replace("dicebound.py", "dicebound_save.txt")
NUM_DICE    = 5
MAX_REROLLS = 3
DICE_FACES  = 6

STARTING_HP     = 1000
STARTING_DAMAGE = 100
STARTING_GOLD   = 0

POISON_DMG_PER_STACK  = 5
HEAL_PER_LEVEL        = 20
CRIT_CHANCE_PER_LEVEL = 5


# --------------------------------------------------
# UI Helpers
# --------------------------------------------------
def print_line():
    print("=" * 38)

def print_header(text):
    print_line()
    print(text)
    print_line()

def press_enter():
    input("\n  [ Press Enter to continue... ]")


# --------------------------------------------------
# Save, Load, and Reset
# --------------------------------------------------
def reset_game():
    return (
        1,                  # player_level
        STARTING_HP,        # player_hp
        STARTING_HP,        # player_max_hp  
        STARTING_GOLD,      # player_gold
        STARTING_DAMAGE,    # player_base_damage
        0,                  # player_total_gold
        [0, 0, 0, 0, 0],    # die_poison
        [0, 0, 0, 0, 0],    # die_critical
        [0, 0, 0, 0, 0],    # die_heal
        0                   # enemy_poison_stacks
    )

def save_game(player_level, player_hp, player_max_hp, player_gold, player_base_damage, player_total_gold, enemy_poison_stacks, die_poison, die_critical, die_heal):
    with open(SAVE_FILE, "w") as file:
        file.write(str(player_level)       + "\n")
        file.write(str(player_hp)          + "\n")
        file.write(str(player_max_hp)      + "\n")  
        file.write(str(player_gold)        + "\n")
        file.write(str(player_base_damage) + "\n")
        file.write(str(player_total_gold)  + "\n")
        file.write(str(enemy_poison_stacks)+ "\n")
        for i in range(NUM_DICE):
            file.write(str(die_poison[i])   + "\n")
        for i in range(NUM_DICE):
            file.write(str(die_critical[i]) + "\n")
        for i in range(NUM_DICE):
            file.write(str(die_heal[i])     + "\n")

    print("  Game saved to: " + SAVE_FILE)

def load_game():
    if exists(SAVE_FILE) == False:
        print("  No save file found.")
        return False, None 

    with open(SAVE_FILE, "r") as file:
        lines = file.readlines()

    player_level        = int(lines[0])
    player_hp           = float(lines[1])
    player_max_hp       = float(lines[2])
    player_gold         = float(lines[3])
    player_base_damage  = float(lines[4])
    player_total_gold   = float(lines[5])
    enemy_poison_stacks = int(lines[6])

    die_poison   = []
    die_critical = []
    die_heal     = []
    
    
    for i in range(NUM_DICE):
        die_poison.append(int(lines[7 + i]))
    for i in range(NUM_DICE):
        die_critical.append(int(lines[12 + i]))
    for i in range(NUM_DICE):
        die_heal.append(int(lines[17 + i]))

    print("  Game loaded!")
    state = (player_level, player_hp, player_max_hp, player_gold, player_base_damage, player_total_gold, die_poison, die_critical, die_heal, enemy_poison_stacks)
    
    return True, state

def delete_save():
    if exists(SAVE_FILE):
        remove(SAVE_FILE)


# --------------------------------------------------
# Enemy Generation
# --------------------------------------------------

def get_enemy(level):
    base_hp  = int(500 * (1.20 ** (level - 1)))
    base_dmg = int(25  * (1.15 ** (level - 1)))

    if level % 10 == 0:
        is_boss = True
        is_mini_boss = False
    elif level % 5 == 0:
        is_boss = False
        is_mini_boss = True
    else:
        is_boss = False
        is_mini_boss = False

    if is_boss:
        hp     = base_hp  * 4
        damage = base_dmg * 3
        name   = "BOSS"
    elif is_mini_boss:
        hp     = int(base_hp  * 2)
        damage = int(base_dmg * 1.5)
        name   = "MINI BOSS"
    else:
        hp     = base_hp
        damage = base_dmg
        name   = "Enemy"

    return (name, hp, hp, damage, is_boss, is_mini_boss)


# --------------------------------------------------
# Rolling and Scoring Dice
# --------------------------------------------------

def roll_dice():
    result = []
    for i in range(NUM_DICE):
        result.append(randrange(1, DICE_FACES + 1))
    return result

def reroll_selected(dice, positions):
    
    # Copy list so we keep the original 
    new_dice = list(dice)
    
    for die_number in positions:
        list_index = die_number - 1
        
        # Roll a new random number for this die
        new_dice[list_index] = randrange(1, DICE_FACES + 1)
        
    return new_dice

def get_dice_positions(user_input):
    chosen_dice = []
    current_text = ""
 
    for i in range(len(user_input)):
        character = user_input[i]
 
        # If we hit a space or the end of the input
        if character == " " or i == len(user_input) - 1:
            
            # If it is the end of the input, we add the last character to text
            if character != " ":
                current_text += character
            
            die_number = int(current_text)
            chosen_dice.append(die_number)
            
            # Reset the text back to blank for the next number
            current_text = ""
            
        else:
            # Keep building the text letter by letter
            current_text += character
 
    return chosen_dice

def display_dice(dice, label):
    
    dice_text = "  [ "
    position_text = "    "
    
    
    for i in range(len(dice)):
        die_value = dice[i]
        die_number = i + 1  
        
        
        dice_text += str(die_value)
        position_text += str(die_number)
        
        # We add spaces if it's not the last die
        if i < len(dice) - 1:
            dice_text += "  "
            position_text += "   "
            
    # After the loop we close the parenthesis
    dice_text += " ]"
    
    # We print it
    print("\n  " + label + ":")
    print(dice_text)

def count_values(dice):
    # Count how many unique numbers
    unique_numbers = []
    
    # Count how many times each number shows up
    face_counts = []
    
    for i in range(len(dice)):
        die_value = dice[i]
        
        # To check if we have already found the number
        already_found = False
        
        # To check if this die already has been shown
        for k in range(len(unique_numbers)):
            if unique_numbers[k] == die_value:
                # If we find the number , we increase the count
                face_counts[k] += 1
                already_found = True  
        
        # If we haven't found the number , we add it to the list
        if already_found == False:
            unique_numbers.append(die_value)
            face_counts.append(1) 
            
    return (unique_numbers, face_counts)

def is_straight(dice):
    # If the dice are 1,2,3,4,5 or 2,3,4,5,6 then it's a straight
    unique = sorted(list(set(dice)))
    return unique == [1, 2, 3, 4, 5] or unique == [2, 3, 4, 5, 6]

def get_combo(dice):
    
    # Get counts of each die value
    result = count_values(dice)
    unique_faces = result[0]
    face_counts = result[1]

    # Sort the counts in descending order to make it easier to check for combos.
    sorted_count = list(face_counts)
    sorted_count.sort()      
    sorted_count.reverse()   

    # Find which face value appeared how many times
    def find_value_with_count(target):
        
        # Loop through every position in our parallel lists
        
        for index in range(len(unique_faces)):
            
            current_face = unique_faces[index]
            current_count = face_counts[index]
            
            if current_count == target:
                return current_face
                
                
        return 0

    # Find where a specific die value is sitting in the dice list
    
    def positions_of_face_value(face_value):
        
        positions_list = []
        
        for index in range(len(dice)):
            if dice[index] == face_value:
                positions_list.append(index)
        return positions_list


    # Checking combos ( Name , Multiplier, Positions that count for the combo ) (Most Damage to Least)

    if sorted_count[0] == 5:
        return ("Five of a Kind", 14.5, [0, 1, 2, 3, 4])
        
    if sorted_count[0] == 4:
        quad_value = find_value_with_count(4)
        return ("Four of a Kind", 9.0, positions_of_face_value(quad_value))
        
    if sorted_count[0] == 3 and len(sorted_count) > 1 and sorted_count[1] == 2:
        return ("Full House", 5.6, [0, 1, 2, 3, 4])
        
    if is_straight(dice) == True:
        return ("Straight", 4.8, [0, 1, 2, 3, 4])
        
    if sorted_count[0] == 3:
        triple_value = find_value_with_count(3)
        return ("Three of a Kind", 4.0, positions_of_face_value(triple_value))


    # Find all pairs 
    pair_values = []
    for index in range(len(unique_faces)):
        if face_counts[index] == 2:
            pair_values.append(unique_faces[index])

    # Two Pair
    if len(pair_values) == 2:
        idx = []
        for index in range(len(dice)):
            # If the die matches either the first pair OR the second pair
            if dice[index] == pair_values[0] or dice[index] == pair_values[1]:
                idx.append(index)
        return ("Two Pair", 3.6, idx)
        
    # One Pair
    if len(pair_values) == 1:
        return ("One Pair", 2.4, positions_of_face_value(pair_values[0]))


    # High Roller: has a 6, but all dice are different

    has_six = False
    for index in range(len(dice)):
        if dice[index] == 6:
            has_six = True
            
    if has_six == True and face_counts[0] == 1:
        return ("High Roller", 1.6, positions_of_face_value(6))


    # If it failed all tests, it's nothing!
    return ("Nothing", 1.0, [])


# --------------------------------------------------
# Upgrades & Mechanics 
# --------------------------------------------------

def apply_poison(scoring_indices, die_poison, enemy_poison_stacks):
    
    new_stacks = 0
    
    for index in scoring_indices:
        
        # Look up the poison upgrade level for this specific die
        current_poison_level = die_poison[index]
        
        # If this die actually has a poison upgrade, add it to our total
        if current_poison_level > 0:
            new_stacks += current_poison_level
            
    # Add the newly applied poison to the enemy's running total
    enemy_poison_stacks += new_stacks
    
    return enemy_poison_stacks, new_stacks

def calc_poison_damage(die_poison, enemy_poison_stacks):
    
    if enemy_poison_stacks == 0:
        return 0
        
    # We create an algorithm to find the highest posion level
    highest_poison = 0
    
    # Check each dies poison level
    for index in range(len(die_poison)):
        current_poison_level = die_poison[index]
        
        if current_poison_level > highest_poison:
            highest_poison = current_poison_level
            
    # If 0 
    if highest_poison == 0:
        return 0
        
    # Calculate the total damage
    total_damage = enemy_poison_stacks * highest_poison * POISON_DMG_PER_STACK
    
    return total_damage

def apply_heal(scoring_indices, die_heal, player_hp, player_max_hp):
    
    total_healed = 0
    
    for index in scoring_indices:
        
        # We check the heal level for this die
        current_heal_level = die_heal[index]
        if current_heal_level > 0:
            
            total_healed += current_heal_level * HEAL_PER_LEVEL
            
    # Total heal is added to the player hp
    player_hp += total_healed
    
    # If the heal put the player over their max hp , we set it back down to the max
    if player_hp > player_max_hp:
        player_hp = player_max_hp
        
    return player_hp, total_healed

def calc_crit(scoring_indices, die_critical):
    
    # We check each die
    for index in scoring_indices:
        
        current_crit_level = die_critical[index]
        
        if current_crit_level > 0:
            
            crit_chance = current_crit_level * CRIT_CHANCE_PER_LEVEL
            
            # We roll a random number between 1 and 100, and if it is less than or equal to our crit chance we hit crit
            roll = randrange(1, 101)
            
            if roll <= crit_chance:
                return True  
                
    
    return False

def upgrade_cost(current_level):
    return current_level * 25 + 25


# --------------------------------------------------
# Displaying 
# --------------------------------------------------

def show_die_upgrades(die_poison, die_critical, die_heal):
    print("\n  Die Upgrades:")
    print(f"  {'-' * 32}")
    
    for index in range(NUM_DICE):
        poison_level = die_poison[index]
        crit_level = die_critical[index]
        heal_level = die_heal[index]
        
        upgrade_text = ""
        
        if poison_level > 0:
            upgrade_text += f"Poison Lv{poison_level}  "
            
        if crit_level > 0:
            upgrade_text += f"Crit Lv{crit_level}  "
            
        if heal_level > 0:
            upgrade_text += f"Heal Lv{heal_level}  "
            
        if upgrade_text == "":
            upgrade_text = "No upgrades"
            
        die_number = index + 1
        
        print(f"    Die {die_number}: {upgrade_text}")
        
    print(f"  {'-' * 32}")

def build_hp_bar(current_hp, max_hp):
    
    bar_width = 20
        
    health_percentage = current_hp / max_hp
    
    filled_blocks = int(health_percentage * bar_width)
    
    if filled_blocks < 0:
        filled_blocks = 0
        
    if filled_blocks > bar_width:
        filled_blocks = bar_width
        
    empty_blocks = bar_width - filled_blocks
    
    filled_text = "█" * filled_blocks
    empty_text = "░" * empty_blocks
    
    return f"[{filled_text}{empty_text}]"

def show_player_stats(player_hp, player_max_hp, player_gold, player_base_damage):
    print(f"  Player HP   : {player_hp} / {player_max_hp}")
    print(f"  Gold        : {player_gold} ")
    print(f"  Base Damage : {player_base_damage}")

def show_enemy_stats(enemy_name, enemy_hp, enemy_max_hp, enemy_poison_stacks):
    
    hp_bar = build_hp_bar(enemy_hp, enemy_max_hp)
    
    print(f"\n  {enemy_name} HP: {enemy_hp} / {enemy_max_hp}")
    
    print(f"  {hp_bar}")
    
    if enemy_poison_stacks > 0:
        print(f"  Poison Stacks: {enemy_poison_stacks}")

def show_level_header(player_level, player_hp, player_max_hp, player_gold, player_base_damage, die_poison, die_critical, die_heal, enemy_name, enemy_hp, enemy_max_hp, enemy_poison_stacks, is_boss, is_mini_boss):
    
    
    print("\n")
    
    
    if is_boss == True:
        print_header(f"  === BOSS FIGHT  --  LEVEL {player_level} ===  ")
        
    elif is_mini_boss == True:
        print_header(f"  === MINI BOSS   --  LEVEL {player_level} ===  ")
        
    else:
        print_header(f"           LEVEL {player_level}           ")

    
    show_player_stats(player_hp, player_max_hp, player_gold, player_base_damage)
    show_die_upgrades(die_poison, die_critical, die_heal)
    show_enemy_stats(enemy_name, enemy_hp, enemy_max_hp, enemy_poison_stacks)

    
    
    

# --------------------------------------------------
# Turn Execution
# --------------------------------------------------

def player_turn(enemy_hp, player_base_damage, player_hp, player_max_hp, enemy_poison_stacks, die_poison, die_critical, die_heal):

    print("\n")
    print("=" * 38)
    print("  YOUR TURN")
    print("=" * 38)

    dice = roll_dice()
    display_dice(dice, "Your dice")

    # Reroll loop 
    
    rerolls_left = MAX_REROLLS
    while rerolls_left > 0:

        print(f"\n  Rerolls left: {rerolls_left}")
        print("  Press Enter to keep your dice.")

        input_ = input("  > ")
        better_input = input_.strip()

        if better_input == "":
            break

        positions = get_dice_positions(better_input)

        if len(positions) == 0:
            print("  No valid positions, keeping dice.")
            break

        if len(positions) > rerolls_left:
            print(f"  Not enough rerolls! ({len(positions)} dice needs {len(positions)} rerolls)")
            continue

        rerolls_left -= len(positions)
        dice = reroll_selected(dice, positions)
        display_dice(dice, "Updated dice")
    
    # Calculate the combo 

    combo_results = get_combo(dice)
    combo_name = combo_results[0]
    multiplier = combo_results[1]
    scoring_idx = combo_results[2]
    
    print(f"\n {combo_name}")
    print(f"  Multiplier : x{multiplier}!")

    is_crit = calc_crit(scoring_idx, die_critical)
    
    if is_crit == True:
        crit_mult = 2
        print("  CRITICAL HIT! Damage doubled!")
    else:
        crit_mult = 1

    # Calculate total damage
    total_damage = int(player_base_damage * multiplier * crit_mult)
    print(f"\n  You dealt {total_damage} damage.")
    enemy_hp -= total_damage

    # All special effects for dies
    
    # Heal
    
    player_hp, healed_amount = apply_heal(scoring_idx, die_heal, player_hp, player_max_hp)
    if healed_amount > 0:
        print(f"  Healed {healed_amount} HP!  ({player_hp} / {player_max_hp})")

    # Poison Stacks
    
    enemy_poison_stacks, newly_added_stacks = apply_poison(scoring_idx, die_poison, enemy_poison_stacks)
    if newly_added_stacks > 0:
        print(f"  Added {newly_added_stacks} poison stack(s)! (total: {enemy_poison_stacks})")

    # Poison damage
    
    poison_damage = calc_poison_damage(die_poison, enemy_poison_stacks)
    if poison_damage > 0:
        print(f"  Poison deals {poison_damage} extra damage.")
        enemy_hp -= poison_damage

    # remaining enemy hp 
    
    if enemy_hp < 0:
        enemy_hp = 0

    return enemy_hp, player_hp, enemy_poison_stacks

def enemy_turn(enemy_name, enemy_damage, player_hp):
    
    print("\n")
    print("=" * 38)
    print("  ENEMY TURN  --  " + enemy_name + " attacks!")
    print("=" * 38)

    player_hp -= enemy_damage
    print("\n  " + enemy_name + " hits you for " + str(enemy_damage) + " damage")
    return max(0, player_hp), player_hp <= 0



# --------------------------------------------------
# After battle shop
# --------------------------------------------------

def show_shop(player_gold, player_base_damage, player_hp, player_max_hp, die_poison, die_critical, die_heal):
    print_header("        UPGRADE SHOP        ")
    
    print(f"\n  Gold: {player_gold} ")
    show_die_upgrades(die_poison, die_critical, die_heal)

    while True:
        print("\n  What would you like to buy?")
        print("    1. Increase Poison level on a die")
        print("    2. Increase Critical level on a die")
        print("    3. Increase Heal level on a die")
        print("    4. Increase Base Damage (+50)  [costs 100 ]")
        print("    5. Heal yourself (+200 HP)     [costs 80 ]")
        print("    6. Skip")

        
        choice = input("\n  Your choice: ")
        better_choice = choice.strip()
        
        if better_choice.isdigit() == False:
            print("  Please enter a valid number.")
            continue

        choice = int(better_choice)

        # Upgrade die
        if choice >= 1 and choice <= 3:
            print(f"\n  Which die slot? (1-{NUM_DICE})")
            
            die_choice = input("  Die number: ")
            better_die_choice = die_choice.strip()
            
            if better_die_choice.isdigit() == False:
                print("  Please enter a valid number.")
                continue
                
            die_choice = int(better_die_choice)
            if die_choice < 1 or die_choice > NUM_DICE:
                print("  Invalid die number.")
                continue

            die_index = die_choice - 1

            if choice == 1:
                current_level = die_poison[die_index]
                upgrade_name = "Poison"
            elif choice == 2:
                current_level = die_critical[die_index]
                upgrade_name = "Critical"
            elif choice == 3:
                current_level = die_heal[die_index]
                upgrade_name = "Heal"

            cost = upgrade_cost(current_level)
            next_level = current_level + 1
            print(f"  Die {die_choice} {upgrade_name} is Lv{current_level}. Upgrade to Lv{next_level} costs {cost} gp.")
            
            # Check if player has enough gold
            if player_gold >= cost:
                player_gold -= cost
                    
                if choice == 1:
                    die_poison[die_index] += 1
                elif choice == 2:
                    die_critical[die_index] += 1
                elif choice == 3:
                    die_heal[die_index] += 1
                        
                print(f"  Die {die_choice} {upgrade_name} upgraded!")
            else:
                print(f"  Not enough gold! (need {cost})")

        # Choice 4
        
        elif choice == 4:
            
            if player_gold >= 100:
                player_gold -= 100
                player_base_damage += 50
                print(f"  Base Damage is now {player_base_damage}!")
            else:
                print("  Not enough gold! (need 100)")

        # Choice 5 
        
        elif choice == 5:
            if player_gold >= 80:
                player_gold -= 80
                
                missing_hp = player_max_hp - player_hp
                heal_amount = 200
                
                if heal_amount > missing_hp:
                    heal_amount = missing_hp
                    
                player_hp += heal_amount
                
                print(f"  Healed {heal_amount} HP!  ({player_hp} / {player_max_hp})")
            
            else:
                
                print("  Not enough gold! (need 80)")

        # Choice 6
        elif choice == 6:
            break

        print(f"\n  Gold remaining: {player_gold}")
        
        continue_ = input("  Buy something else? (y/n): ")
        if continue_.strip() != "y":
            break

    return player_gold, player_base_damage, player_hp, die_poison, die_critical, die_heal

def post_victory(player_level, player_gold, player_total_gold, player_hp, player_max_hp, player_base_damage, die_poison, die_critical, die_heal):
    
    gold_earned = player_level * 10
    
    player_gold += gold_earned
    
    player_total_gold += gold_earned

    print_header("           VICTORY!           ")
    

    print(f"\n  You earned {gold_earned} gold!")
    print(f"  Total gold: {player_total_gold}")
    
    press_enter()

    shop_results = show_shop(player_gold, player_base_damage, player_hp, player_max_hp, die_poison, die_critical, die_heal)
    
    # Update player stats based on the shop results
    player_gold        = shop_results[0]
    player_base_damage = shop_results[1]
    player_hp          = shop_results[2]
    die_poison         = shop_results[3]
    die_critical       = shop_results[4]
    die_heal           = shop_results[5]

    # Level up for the next round
    player_level += 1
    
    # Return all the updated stats back to the main game loop
    return player_level, player_gold, player_total_gold, player_hp, player_base_damage, die_poison, die_critical, die_heal


# --------------------------------------------------
# Main Algorithm LOOPS
# --------------------------------------------------

def run_battle(player_level, player_hp, player_max_hp, player_gold, player_base_damage, die_poison, die_critical, die_heal):
    
    # --- DÜŞMAN BİLGİLERİNİ ÇEKME ---
    # get_enemy fonksiyonundan gelen dev paketi manuel olarak açıyoruz
    enemy_data = get_enemy(player_level)
    enemy_name   = enemy_data[0]
    enemy_hp     = enemy_data[1]
    enemy_max_hp = enemy_data[2]
    enemy_damage = enemy_data[3]
    is_boss      = enemy_data[4]
    is_mini_boss = enemy_data[5]
    
    enemy_poison_stacks = 0 

    # Savaş bir taraf ölene kadar devam eder
    while True:
        show_level_header(player_level, player_hp, player_max_hp, player_gold, player_base_damage, die_poison, die_critical, die_heal, enemy_name, enemy_hp, enemy_max_hp, enemy_poison_stacks, is_boss, is_mini_boss)
        
        press_enter()

        # Player turn
        
        turn_results = player_turn(enemy_hp, player_base_damage, player_hp, player_max_hp, enemy_poison_stacks, die_poison, die_critical, die_heal)
        enemy_hp            = turn_results[0]
        player_hp           = turn_results[1]
        enemy_poison_stacks = turn_results[2]

        # Check if enemy is defeated
        
        if enemy_hp <= 0:
            
            print(f"\n  {enemy_name} was defeated!")
            press_enter()
        
            return True, player_hp, enemy_poison_stacks

        # Print remaining enemy HP 
        print(f"\n  {enemy_name} has {enemy_hp} HP left.")
        press_enter()

        # Enemy turn
        
        enemy_turn_results = enemy_turn(enemy_name, enemy_damage, player_hp)
        player_hp   = enemy_turn_results[0]
        player_died = enemy_turn_results[1]

        #  Check if player is defeated
        if player_died == True:
            print("\n  You were defeated...")
            press_enter()
            
            return False, player_hp, enemy_poison_stacks

        # If both is still alive , continue the loop
        print(f"\n  Your HP: {player_hp} / {player_max_hp}")
        press_enter()

        # Decrease poison stacks by 35% turn
        enemy_poison_stacks = int(enemy_poison_stacks * 0.35)


def game_loop(state):
    
    # Getting player stats 
    
    player_level        = state[0]
    player_hp           = state[1]
    player_max_hp       = state[2]
    player_gold         = state[3]
    player_base_damage  = state[4]
    player_total_gold   = state[5]
    die_poison          = state[6]
    die_critical        = state[7]
    die_heal            = state[8]
    enemy_poison_stacks = state[9]

    # Continue until the player or the enemy dies
    while True:
        
        # Get battle results
        battle_results = run_battle(player_level, player_hp, player_max_hp, player_gold, player_base_damage, die_poison, die_critical, die_heal)
        
        won                 = battle_results[0]
        player_hp           = battle_results[1]
        enemy_poison_stacks = battle_results[2]

        # If defeated 
        
        if won == False:
            print("\n\n")
            print_header("          GAME OVER          ")
            
            print(f"\n  You reached Level {player_level}.")
            print(f"  Total gold earned: {player_total_gold} gp\n")
            
            delete_save()
            press_enter()
            
            return


        
        victory_results = post_victory(player_level, player_gold, player_total_gold, player_hp, player_max_hp, player_base_damage, die_poison, die_critical, die_heal)
        
        player_level       = victory_results[0]
        player_gold        = victory_results[1]
        player_total_gold  = victory_results[2]
        player_hp          = victory_results[3]
        player_base_damage = victory_results[4]
        die_poison         = victory_results[5]
        die_critical       = victory_results[6]
        die_heal           = victory_results[7]
        
        # Save game before next battle
        save_game(player_level, player_hp, player_max_hp, player_gold, player_base_damage, player_total_gold, enemy_poison_stacks, die_poison, die_critical, die_heal)


def main_menu():
    
    print("\n\n")
    
    print_header("          D I C E B O U N D         ")
    print("\n  Roll dice.\n  Deal damage.\n  Upgrade.\n  Survive.")
    print("\n  1. New Game")
    print("  2. Load Game")
    print("  3. Quit\n")

    while True:
        
        choice_ = input("  Your choice: ")
        better_choice = choice_.strip()
        
        if better_choice == "1":
            new_state = reset_game()
            
            return True, new_state
            

        elif better_choice == "2":
            
            load_results = load_game()
            success = load_results[0]
            current_state = load_results[1]
            
            # If loading failed , start new game
            if success == False:
                print("  Starting a new game...")
                current_state = reset_game()
                
            return True, current_state
            
        elif better_choice == "3":
            return False, None

        # Invalid    
        else:
            print("  Please enter 1, 2, or 3.")


# --------------------------------------------------
# Starting the game
# --------------------------------------------------


while True:
    
    menu_results = main_menu()
    keep_playing = menu_results[0]
    initial_game_state = menu_results[1]
    
    if keep_playing == False:
        print("\n  Thanks for playing! Goodbye.\n")
        
        break
    
    game_loop(initial_game_state)