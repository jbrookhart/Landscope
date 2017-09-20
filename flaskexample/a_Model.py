def ModelIt(fromUser  = 'Default', plants = []):
  in_month = len(plants)
  print 'The number born is %i' % in_month
  result = in_month
  if fromUser != 'Default':
    return result
  else:
    return 'check your input'