# gui_do is a package composed of the gui directory.  Use that package for client programs
if __name__ == '__main__':
    # if this file is launched then start the demo
    from demo.demo import Demo
    Demo().run()
