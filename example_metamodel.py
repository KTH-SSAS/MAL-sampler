def example_metamodel(size_factor=10, initial_asset_type='network'):

      network_n = {'distribution': 'BinomialPlusOne',
                        'n': 1*size_factor,
                        'p': 0.5}

      network_associated_assets = {
                        'network': {'distribution': 'BinomialPlusOne',
                                    'n': 10,
                                    'p': 0.1},
                        'vm_instance': {'distribution': 'Binomial',
                                    'n': 10*size_factor,
                                    'p': 0.05}}
      network_visualization = {'shape': 's',
                                    'color': 'red'}

      vm_instance_n = {'distribution': 'BinomialPlusOne',
                        'n': 5*size_factor,
                        'p': 0.5}
      vm_instance_associated_assets = {
            'network': {'distribution': 'Constant',
                        'n': 1},
            'admin_privileges': {'distribution': 'Constant',
                              'n': 1}}
      vm_instance_visualization = {'shape': 'o',
                                    'color': 'blue'}

      admin_privileges_n = {'distribution': 'BinomialPlusOne',
                              'n': 5*size_factor,
                              'p': 0.5}

      admin_privileges_associated_assets = {
            'vm_instance': {'distribution': 'Constant',
                              'n': 1},
            'principal': {'distribution': 'BinomialPlusOne',
                        'n': 10,
                        'p': 0.1}}

      admin_privileges_visualization = {'shape': 'v',
                                          'color': 'yellow'}

      principal_n = {'distribution': 'BinomialPlusOne',
                        'n': 10*size_factor,
                        'p': 0.05}

      principal_associated_assets = {
            'admin_privileges': {'distribution': 'Binomial',
                              'n': 2*size_factor,
                              'p': 0.1}}

      principal_visualization = {'shape': '^',
                                    'color': 'green'}

      network = {'abbreviation': 'N',
                  'associated_assets': network_associated_assets,
                  'visualization': network_visualization}

      vm_instance = {'abbreviation': 'VM',
                  'associated_assets': vm_instance_associated_assets,
                  'visualization': vm_instance_visualization}

      admin_privileges = {'abbreviation': 'A',
                        'associated_assets': admin_privileges_associated_assets,
                        'visualization': admin_privileges_visualization}
 
      principal = {'abbreviation': 'P',
                  'associated_assets': principal_associated_assets,
                  'visualization': principal_visualization}


      if initial_asset_type == 'network':
            network = {'abbreviation': 'N',
                  'n': network_n,
                  'associated_assets': network_associated_assets,
                  'visualization': network_visualization}

      elif initial_asset_type == 'vm_instance':
            vm_instance = {'abbreviation': 'VM',
                        'n': vm_instance_n,
                        'associated_assets': vm_instance_associated_assets,
                        'visualization': vm_instance_visualization}

      elif initial_asset_type == 'admin_privileges':
            admin_privileges = {'abbreviation': 'A',
                              'n': admin_privileges_n,
                              'associated_assets': admin_privileges_associated_assets,
                              'visualization': admin_privileges_visualization}
            
      elif initial_asset_type == 'principal':
            principal = {'abbreviation': 'P',
                        'n': principal_n,
                        'associated_assets': principal_associated_assets,
                        'visualization': principal_visualization}

      else:
            network = {'abbreviation': 'N',
                  'n': network_n,
                  'associated_assets': network_associated_assets,
                  'visualization': network_visualization}
      
            vm_instance = {'abbreviation': 'VM',
                        'n': vm_instance_n,
                        'associated_assets': vm_instance_associated_assets,
                        'visualization': vm_instance_visualization}

            admin_privileges = {'abbreviation': 'A',
                              'n': admin_privileges_n,
                              'associated_assets': admin_privileges_associated_assets,
                              'visualization': admin_privileges_visualization}

            principal = {'abbreviation': 'P',
                        'n': principal_n,
                        'associated_assets': principal_associated_assets,
                        'visualization': principal_visualization}

      metamodel = {'network': network,
                                          'vm_instance': vm_instance,
                                          'admin_privileges': admin_privileges,
                                          'principal': principal}

      return metamodel
