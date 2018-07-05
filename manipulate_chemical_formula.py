


  def _Remove_punctuation(string):

      """Remove punctuation from string."""

      return string.replace("-","").replace("'","").replace("_","").replace("A","").replace("X","").replace("+","")


  def _Count_elements(moiety):

      """
      Returns dict with keys of elements and
      values of number of elements.
      """

      ret = []
      ans = re.findall(r'([A-Z][a-z]*)(\d*)', moiety)
      for i, value in enumerate(ans):
          val1 = value[1]
          if len(val1) == 0: val1 = 1
          ret.append((unicode(value[0]), int(val1)))

      return collections.OrderedDict(ret)


  def _Counted_elements_to_formula(ordered_dict):

      """
      Takes an ordered dict of counted elements from
      formula and returns a string.
      """

      string = ""
      for key in ordered_dict:
          string += key
          string += str(ordered_dict[key])

      return string


  def _Remove_reagent_ion(formula, reagent_ion):

      """Takes a chemical formula string
      and removes the reagent ion.
      """

      assert reagent_ion in formula,
       "reagent_ion not in formula: %s" %formula

      formula = formula.replace(".","")

      split_formula = _Count_elements(formula)
      for element in split_formula:
          if element == reagent_ion:
              split_formula[element] -= 1
              if split_formula[element] == 0:
                  del split_formula[element]

      return split_formula


  def _Add_reagent_ion(formula, RI):

      """
      Takes a chemical formula string
      and adds in the reagent ion.
      """

      formula = formula.replace(".","")

      count_dict = _Count_elements(formula)
      if RI in count_dict.keys():
          count_dict[RI] += 1
      else:
          count_dict[RI] = 1

      return count_dict


  def _Mass_calculator(moiety):

      """Calculates exact mass for a given formula (string)."""
      return mass.calculate_mass(formula = moiety)



  def remove_RI(formula, reagent_ion):

      "Takes string and returns string with RI removed."

      return _Counted_elements_to_formula(_Remove_reagent_ion(formula, reagent_ion))


  def add_RI(formula, reagent_ion):

      "Takes string and returns string with RI Added."

      return _Counted_elements_to_formula(_Add_reagent_ion(formula, reagent_ion))
