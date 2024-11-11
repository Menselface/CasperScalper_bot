async def find_only_integer(text: str) -> float:
    text = text.strip().split()
    money = 0
    for string in text:
        try:
            money += float(string)
        except ValueError:
            return False
    
    return float(money)


async def find_only_integer_int(text: str) -> float:
    text = text.strip().split()
    money = 0
    for string in text:
        if string.isdecimal():
            money += int(string)
        
        else:
            try:
                if string:
                    money += int(string)
                    return money
            except ValueError:
                return False
    
    return float(money)
